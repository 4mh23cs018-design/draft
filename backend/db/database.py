from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from backend.core.config import settings
from backend.core.logging import logger

Base = declarative_base()

# Async Engine for FastAPI
async_engine = None
AsyncSessionLocal = None

def init_db_engine():
    global async_engine, AsyncSessionLocal
    db_url = settings.DATABASE_URL
    
    # If SQLite or local override for testing
    if db_url.startswith("sqlite"):
        async_engine = create_async_engine(db_url, echo=False)
    else:
        async_engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

init_db_engine()

async def get_db():
    """Dependency for obtaining async DB sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
