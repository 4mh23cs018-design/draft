from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.db.database import get_db
from backend.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    GET /health
    System health status check verifying database connection and embedding mode.
    """
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    has_openai = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "embedding_provider": "OpenAI" if has_openai else "Mock/Offline",
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "top_k": settings.TOP_K
    }
