from typing import List
from openai import AsyncOpenAI
from backend.embeddings.base import BaseEmbeddingService
from backend.core.config import settings
from backend.core.logging import logger

class OpenAIEmbeddingService(BaseEmbeddingService):
    """OpenAI Embedding Service using text-embedding-3-small."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self._client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def embed_text(self, text: str) -> List[float]:
        if not self._client:
            raise ValueError("OpenAI API key is missing. Set OPENAI_API_KEY in environment or .env.")
        response = await self._client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self._client:
            raise ValueError("OpenAI API key is missing. Set OPENAI_API_KEY in environment or .env.")
        # Process in batches of 64
        batch_size = 64
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self._client.embeddings.create(
                input=batch,
                model=self.model
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
        return all_embeddings

    @property
    def dimension(self) -> int:
        return 1536
