from fastapi import APIRouter
from multiprocessing import Process
from api.services.indexer.orchestrator import run_indexing_pipeline

router = APIRouter()

@router.post("/api/system/vectorindexer/run")
async def trigger_vector_indexer_api():
    from api.tasks import run_indexer_job
    run_indexer_job.delay()
    return {"message": "✅ AI 벡터 인덱싱 작업이 Redis 큐에 성공적으로 등록되었습니다."}
