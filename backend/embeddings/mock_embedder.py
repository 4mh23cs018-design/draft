import hashlib
import math
from typing import List
from backend.embeddings.base import BaseEmbeddingService

class MockEmbeddingService(BaseEmbeddingService):
    """Deterministic Mock Embedding Service for local testing without an API key."""

    def __init__(self, dimension: int = 1536):
        self._dim = dimension

    def _generate_vector(self, text: str) -> List[float]:
        # Generate deterministic pseudo-random seed from string hash
        hash_digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(hash_digest[:4], "big")

        vector = []
        for i in range(self._dim):
            # Modular linear congruential generator
            val = math.sin(seed + i * 0.1)
            vector.append(val)

        # Normalize to unit length for cosine similarity calculations
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self._dim
