from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.retrieval.vector_search import VectorSearchEngine
from backend.retrieval.keyword_search import KeywordSearchEngine
from backend.core.config import settings

class HybridSearchEngine:
    """Hybrid Retrieval engine executing Vector and Keyword search fused via Reciprocal Rank Fusion (RRF)."""

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        query: str,
        query_vector: List[float],
        top_k: int = 5,
        document_id: Optional[str] = None,
        vector_weight: float = None,
        keyword_weight: float = None
    ) -> List[Dict[str, Any]]:
        v_weight = vector_weight if vector_weight is not None else settings.VECTOR_WEIGHT
        k_weight = keyword_weight if keyword_weight is not None else settings.KEYWORD_WEIGHT

        # Retrieve top 2*k from vector and keyword search
        fetch_k = top_k * 2

        vector_results = await VectorSearchEngine.search(
            session=session,
            query_vector=query_vector,
            top_k=fetch_k,
            document_id=document_id
        )

        keyword_results = await KeywordSearchEngine.search(
            session=session,
            query=query,
            top_k=fetch_k,
            document_id=document_id
        )

        # RRF score accumulation
        rrf_constant = 60.0
        chunk_map: Dict[str, Dict[str, Any]] = {}
        rrf_scores: Dict[str, float] = {}

        # Process vector ranks
        for rank, item in enumerate(vector_results):
            cid = item["chunk_id"]
            chunk_map[cid] = item
            score_contribution = v_weight * (1.0 / (rrf_constant + rank + 1))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score_contribution

        # Process keyword ranks
        for rank, item in enumerate(keyword_results):
            cid = item["chunk_id"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            score_contribution = k_weight * (1.0 / (rrf_constant + rank + 1))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score_contribution

        # Sort chunks by final RRF score
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        final_results = []
        for cid in sorted_chunk_ids[:top_k]:
            chunk_info = dict(chunk_map[cid])
            chunk_info["rrf_score"] = rrf_scores[cid]
            chunk_info["search_type"] = "hybrid"
            final_results.append(chunk_info)

        return final_results
