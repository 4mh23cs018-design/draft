from fastapi import APIRouter
from backend.eval.metrics import EvaluationTracker

router = APIRouter(prefix="/eval", tags=["evaluation"])

@router.get("/metrics")
async def get_evaluation_metrics():
    """
    GET /eval/metrics
    Retrieves global RAG evaluation metrics summary including latencies, tokens, and precision.
    """
    return EvaluationTracker.get_summary_metrics()
