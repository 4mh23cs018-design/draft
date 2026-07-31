import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Production RAG Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""

    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4o-mini"

    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/rag_db"

    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5

    # Hybrid & Reranking Settings
    HYBRID_SEARCH_ENABLED: bool = True
    VECTOR_WEIGHT: float = 0.6
    KEYWORD_WEIGHT: float = 0.4
    RERANK_ENABLED: bool = False
    RERANK_PROVIDER: str = "score"  # "cohere", "bge", "jina", "score"
    COHERE_API_KEY: str = ""
    RERANK_API_URL: str = ""

    # Security & File Limits
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md", ".html", ".htm"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
