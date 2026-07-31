from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingService(ABC):
    """Abstract interface for vector embedding generation."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate vector embedding for a single string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of strings."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        pass
