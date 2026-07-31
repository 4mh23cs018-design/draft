from backend.embeddings.base import BaseEmbeddingService
from backend.embeddings.openai_embedder import OpenAIEmbeddingService
from backend.embeddings.mock_embedder import MockEmbeddingService
from backend.core.config import settings

def get_embedding_service() -> BaseEmbeddingService:
    """Factory function returning active embedding provider."""
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
        return OpenAIEmbeddingService()
    return MockEmbeddingService()
