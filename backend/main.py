from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.core.config import settings
from backend.core.logging import logger
from backend.db.database import async_engine, Base
from backend.api.routes import documents, chat, health, eval

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle event handler."""
    logger.info("Initializing RAG application startup...")
    
    # Auto-create tables for local execution/testing if Postgres vector or SQLite
    try:
        async with async_engine.begin() as conn:
            if async_engine.dialect.name == "postgresql":
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization notice: {str(e)}")

    yield
    
    logger.info("Shutting down RAG application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
from fastapi.responses import RedirectResponse

app.include_router(documents.router, tags=["Documents"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(health.router, tags=["Health"])
app.include_router(eval.router, tags=["Evaluation"])

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
