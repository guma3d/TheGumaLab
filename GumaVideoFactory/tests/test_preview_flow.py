import asyncio
import tempfile
import unittest
from pathlib import Path
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
                        patch.object(main, "IMAGES_DIR", self.root)]
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
        req = main.ReviewRequest(narrations=["수정 대본"]*6, approved=True)
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
            self.assertEqual(images.call_count, 5)
        self.assertEqual(main.load_project(p["id"])["status"], "preview_ready")

    def test_missing_preview_blocks_approval(self):
        p = self.create()
        self.prepare(p)
        main.preview_image_path(p["id"], 2).unlink()
        with self.assertRaises(HTTPException):
            asyncio.run(main.start_generation(p["id"], main.ReviewRequest(narrations=["test"]*6, approved=True), BackgroundTasks()))

    def test_rendered_preview_and_approved_images_reach_video_generation(self):
        p = self.create()
        self.prepare(p)
        with TestClient(main.app) as client:
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.text.count('class="input-textarea scene-narration"'), 6)
            self.assertIn("최종 승인하고 영상 만들기", page.text)
            self.assertIn("gemini-3.8-flash + Veo 3.1", page.text)
        asyncio.run(main.start_generation(p["id"], main.ReviewRequest(narrations=["수정"]*6, approved=True), BackgroundTasks()))
        with patch.object(main, "generate_video_clip") as video, patch.object(main, "synthesize_speech", new_callable=AsyncMock) as speech, patch.object(main, "concatenate_clips_with_audio"):
            asyncio.run(main.async_generate_video(p["id"]))
            self.assertEqual(video.call_count, 6)
            self.assertEqual(video.call_args_list[0].kwargs["image_path"], main.preview_image_path(p["id"], 1))
            self.assertEqual(speech.call_args.args[0], " ".join(["수정"]*6))
        self.assertEqual(main.load_project(p["id"])["status"], "ready")


if __name__ == "__main__":
    unittest.main()
