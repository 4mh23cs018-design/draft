from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx
from backend.core.config import settings
from backend.core.logging import logger

class BaseReranker(ABC):
    """Abstract interface for document reranking engines."""

    @abstractmethod
    async def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank chunks based on deep relevance to query."""
        pass

class ScoreReranker(BaseReranker):
    """Default pass-through reranker sorting by existing similarity or RRF score."""

    async def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        sorted_chunks = sorted(
            chunks,
            key=lambda x: x.get("rrf_score", x.get("score", 0.0)),
            reverse=True
        )
        return sorted_chunks[:top_k]

class CohereReranker(BaseReranker):
    """Cohere Rerank API integration."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.COHERE_API_KEY

    async def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        if not self.api_key or not chunks:
            return ScoreReranker().rerank(query, chunks, top_k)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cohere.ai/v1/rerank",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "rerank-english-v3.0",
                        "query": query,
                        "documents": [c["content"] for c in chunks],
                        "top_n": top_k
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    reranked = []
                    for item in data.get("results", []):
                        idx = item["index"]
                        relevance_score = item["relevance_score"]
                        chunk = dict(chunks[idx])
                        chunk["rerank_score"] = relevance_score
                        reranked.append(chunk)
                    return reranked
        except Exception as e:
            logger.error(f"Cohere reranking failed, falling back to score reranker: {str(e)}")

        return await ScoreReranker().rerank(query, chunks, top_k)

class BGEJinaReranker(BaseReranker):
    """Generic HTTP Reranker for BGE / Jina Rerank endpoints."""

    def __init__(self, endpoint_url: str = None, api_key: str = None):
        self.endpoint_url = endpoint_url or settings.RERANK_API_URL
        self.api_key = api_key

    async def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        if not self.endpoint_url or not chunks:
            return await ScoreReranker().rerank(query, chunks, top_k)

        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                response = await client.post(
                    self.endpoint_url,
                    headers=headers,
                    json={
                        "query": query,
                        "documents": [c["content"] for c in chunks],
                        "top_k": top_k
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    results = response.json()
                    reranked = []
                    for item in results:
                        idx = item["index"]
                        chunk = dict(chunks[idx])
                        chunk["rerank_score"] = item.get("score", 0.0)
                        reranked.append(chunk)
                    return reranked
        except Exception as e:
            logger.error(f"BGE/Jina reranking failed: {str(e)}")

        return await ScoreReranker().rerank(query, chunks, top_k)

class RerankerFactory:
    @staticmethod
    def get_reranker() -> BaseReranker:
        if settings.RERANK_ENABLED:
            provider = settings.RERANK_PROVIDER.lower()
            if provider == "cohere":
                return CohereReranker()
            elif provider in ["bge", "jina"]:
                return BGEJinaReranker()
        return ScoreReranker()
