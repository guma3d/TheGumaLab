import asyncio
import tempfile
import unittest
from pathlib import Path
from io import BytesIO
from PIL import Image
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import BackgroundTasks, HTTPException
from app import main
from app.core.planner import VideoStoryBoard, ScenePlan


class PreviewFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patches = [patch.object(main, "PROJECTS_DIR", self.root),
                        patch.object(main, "IMAGES_DIR", self.root),
                        patch.object(main, "PRODUCT_IMAGES_DIR", self.root),
                        patch("app.core.source_media.SOURCE_MEDIA_DIR", self.root)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def create(self):
        return asyncio.run(main.create_project(main.CreateProjectRequest(idea="test"), BackgroundTasks()))

    def board(self):
        return VideoStoryBoard(title="test", summary="test", estimated_total_seconds=24,
            scenes=[ScenePlan(scene_number=i, camera_movement="slow", visual_prompt="scene", narration_ko="대본") for i in range(1, 7)])

    @staticmethod
    def fake_image(prompt, path, *args):
        path.write_bytes(b"test image")
        return path

    def prepare(self, project):
        with patch.object(main, "plan_video_storyboard", return_value=self.board()), patch.object(main, "generate_preview_image", side_effect=self.fake_image):
            asyncio.run(main.async_plan_and_prepare(project["id"]))

    def upload(self, p):
        photo=BytesIO()
        Image.new("RGB", (100, 100), "white").save(photo, format="PNG")
        with TestClient(main.app) as client:
            response=client.post(f"/api/projects/{p['id']}/product-image", files={"file":("product.png",photo.getvalue(),"image/png")})
            self.assertEqual(response.status_code,200)

    def test_preview_then_explicit_approval_and_duplicate_guard(self):
        p = self.create()
        with patch.object(main, "generate_video_clip") as video:
            self.prepare(p)
            video.assert_not_called()
        preview = main.load_project(p["id"])
        self.assertEqual(preview["status"], "preview_ready")
        self.assertEqual(len(preview["storyboard"]["scenes"]), 6)
        with self.assertRaises(HTTPException):
            asyncio.run(main.start_generation(p["id"], main.ReviewRequest(narrations=["new"]*6), BackgroundTasks()))
        tasks = BackgroundTasks()
        self.upload(p)
        req = main.ReviewRequest(narrations=["수정 대본"]*6, approved=True, product_url="https://example.com/product")
        asyncio.run(main.start_generation(p["id"], req, tasks))
        saved = main.load_project(p["id"])
        self.assertEqual(saved["status"], "generating")
        self.assertEqual(saved["storyboard"]["scenes"][0]["narration_ko"], "수정 대본")
        self.assertTrue(saved["approved_at"])
        self.assertEqual(len(tasks.tasks), 1)
        with self.assertRaises(HTTPException):
            asyncio.run(main.start_generation(p["id"], req, BackgroundTasks()))

    def test_failed_images_resume_without_regenerating_completed_cut(self):
        p = self.create()
        def fail_second(prompt, path, *args):
            if '02' in path.name:
                raise RuntimeError("mock failure")
            return self.fake_image(prompt, path)
        with patch.object(main, "plan_video_storyboard", return_value=self.board()), patch.object(main, "generate_preview_image", side_effect=fail_second):
            asyncio.run(main.async_plan_and_prepare(p["id"]))
        self.assertEqual(main.load_project(p["id"])["status"], "preview_failed")
        with patch.object(main, "generate_preview_image", side_effect=self.fake_image) as images:
            asyncio.run(main.retry_preview(p["id"], BackgroundTasks()))
            asyncio.run(main.prepare_preview_images(p["id"]))
            self.assertEqual(images.call_count, 4)
        self.assertEqual(main.load_project(p["id"])["status"], "preview_ready")

    def test_missing_preview_blocks_approval(self):
        p = self.create()
        self.prepare(p)
        main.preview_image_path(p["id"], 2).unlink()
        with self.assertRaises(HTTPException):
            asyncio.run(main.start_generation(p["id"], main.ReviewRequest(narrations=["test"]*6, approved=True), BackgroundTasks()))

    def test_tabs_isolate_projects_and_photo_link_are_required(self):
        tech=self.create()
        food=asyncio.run(main.create_project(main.CreateProjectRequest(idea="food-only-project", category="food"), BackgroundTasks()))
        with TestClient(main.app) as client:
            tech_page=client.get("/?category=tech").text
            food_page=client.get("/?category=food").text
            self.assertNotIn(f'id="card-{food["id"]}"',tech_page)
            self.assertNotIn(f'id="card-{tech["id"]}"',food_page)
            self.assertIn(f'id="card-{food["id"]}"',food_page)
            self.assertEqual(client.get("/?category=unknown").status_code,404)
        self.prepare(tech)
        req=main.ReviewRequest(narrations=["test"]*6,approved=True,product_url="https://example.com")
        with self.assertRaises(HTTPException):
            asyncio.run(main.start_generation(tech['id'],req,BackgroundTasks()))
        self.upload(tech)
        req.product_url=""
        with self.assertRaises(HTTPException):
            asyncio.run(main.start_generation(tech['id'],req,BackgroundTasks()))

    def test_recommendation_snapshot_and_real_food_generation(self):
        item=dict(id="recommendation",category="food",subject="verified food",facts=["evidence"])
        with patch.object(main,"load_daily",return_value={"items":[item]}):
            p=asyncio.run(main.create_project(main.CreateProjectRequest(idea="food",category="food",recommendation_id="recommendation"),BackgroundTasks()))
            with self.assertRaises(HTTPException):
                asyncio.run(main.create_project(main.CreateProjectRequest(idea="tech",category="tech",recommendation_id="recommendation"),BackgroundTasks()))
        self.assertEqual(main.load_project(p['id'])['recommendation']['facts'],['evidence'])
        with patch.object(main,"plan_video_storyboard",return_value=self.board()), patch.object(main,"generate_preview_image",side_effect=AssertionError("Food must not generate images")) as image:
            asyncio.run(main.async_plan_and_prepare(p["id"]))
            image.assert_not_called()
        photo=BytesIO(); Image.new('RGB',(80,60),'orange').save(photo,format='PNG')
        metadata=dict(title='real food',source_url='https://example.com/source',creator='tester',license='CC BY',license_url='https://creativecommons.org/licenses/by/4.0/',attribution='tester, CC BY 4.0')
        with TestClient(main.app) as client:
            for number in range(1,6):
                res=client.post(f"/api/projects/{p['id']}/scenes/{number}/media",files={'file':('food.png',photo.getvalue(),'image/png')},data={'metadata':__import__('json').dumps(metadata)})
                self.assertEqual(res.status_code,200,res.text)
        self.upload(p)
        asyncio.run(main.start_generation(p['id'],main.ReviewRequest(narrations=['test']*6,approved=True,product_url="https://example.com"),BackgroundTasks()))
        with patch.object(main,"generate_video_clip") as video, patch.object(main,"synthesize_speech",new_callable=AsyncMock), patch.object(main,"concatenate_clips_with_audio"), patch.object(main,"render_product_still"), patch.object(main,"render_source_clip") as real:
            asyncio.run(main.async_generate_video(p['id']))
            video.assert_not_called()
            self.assertEqual(real.call_count,5)
            self.assertIn('CC BY', (main.OUTPUTS_DIR/f"{p['id']}_credits.txt").read_text())
            (main.OUTPUTS_DIR/f"{p['id']}_credits.txt").unlink()

    def test_rendered_preview_and_approved_images_reach_video_generation(self):
        p = self.create()
        self.prepare(p)
        with TestClient(main.app) as client:
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.text.count('class="input-textarea scene-narration"'), 6)
            self.assertIn("최종 승인하고 영상 만들기", page.text)
            self.assertIn("gemini-3.8-flash + Veo 3.1", page.text)
        self.upload(p)
        asyncio.run(main.start_generation(p["id"], main.ReviewRequest(narrations=["수정"]*6, approved=True, product_url="https://example.com/product"), BackgroundTasks()))
        with patch.object(main, "generate_video_clip") as video, patch.object(main, "synthesize_speech", new_callable=AsyncMock) as speech, patch.object(main, "concatenate_clips_with_audio"), patch.object(main, "render_product_still") as still:
            asyncio.run(main.async_generate_video(p["id"]))
            self.assertEqual(video.call_count, 5)
            still.assert_called_once()
            self.assertEqual(video.call_args_list[0].kwargs["image_path"], main.preview_image_path(p["id"], 1))
            self.assertEqual(speech.call_args.args[0], " ".join(["수정"]*6))
        self.assertEqual(main.load_project(p["id"])["status"], "ready")


if __name__ == "__main__":
    unittest.main()
