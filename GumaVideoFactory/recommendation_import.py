"""Usage: python recommendation_import.py <researched_batch.json>"""
import sys
from pathlib import Path
from app.core.recommendations import DailyBatch, save_batch
from app.core.categories import PRESETS
from app.core.source_media import download_media, download_youtube_cc

if __name__ == "__main__":
    batch = DailyBatch.model_validate_json(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    from app.core import versions as store
    from app.core.prepared_packages import verify_package
    for item in batch.items:
        if True:
            previews=store.history(item.stable_id(),'Preview')
            if not previews or previews[0].get('status')!='ready' or not previews[0].get('package_ready'):
                raise ValueError(item.subject+': 컷씬·고정 음성·비공개 영상 준비가 끝나야 추천할 수 있습니다.')
            package=verify_package(item.stable_id(),previews[0]['number'])
            if package.get('pipeline')!='shopping_v2':raise ValueError('새 쇼핑쇼츠 컷씬이 필요합니다.')
            videos=store.history(item.stable_id(),'Video')
            if not videos or videos[0].get('publication_state') not in ('private','publish_requested','public') or videos[0].get('preview_version')!=previews[0]['number']:
                raise ValueError('비공개 업로드가 끝난 묶음만 추천합니다.')
    for item in batch.items:
        for source in item.media_sources:
            # 입력 JSON의 경로를 신뢰하지 않고 직접 확보한 파일만 연결합니다.
            source.local_file = ""
            if source.download_url or source.provider == "youtube_cc":
                try:
                    source.local_file = download_youtube_cc(source) if source.provider == "youtube_cc" else download_media(source)
                except Exception as error:
                    print(f"{item.subject}: 자료 자동 확보 실패 ({type(error).__name__}), 프리뷰에서 등록 필요")
    result = save_batch(batch)
    categories = ' / '.join(f"{PRESETS[category]['label']} 3개" for category in PRESETS if any(item.category == category for item in batch.items))
    print(f"{result['date']}: {categories} 저장 완료 (오늘 {result['research_count']}회 조사)")
