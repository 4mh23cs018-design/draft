import math
from typing import List, Dict, Any, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import DocumentChunkModel, DocumentModel
from backend.core.logging import logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Fallback cosine similarity calculation for non-pgvector backends."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class VectorSearchEngine:
    """Vector similarity search engine using pgvector cosine distance."""

    @staticmethod
    async def search(
        session: AsyncSession,
        query_vector: List[float],
        top_k: int = 5,
        document_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes vector similarity search with optional metadata filtering.
        Returns list of dicts with chunk details, metadata, and similarity score.
        """
        try:
            dialect_name = session.bind.dialect.name if session.bind else ""
        except Exception:
            dialect_name = ""
        is_postgres = dialect_name == "postgresql"

        if is_postgres:
            stmt = select(
                DocumentChunkModel,
                DocumentModel.filename,
                DocumentChunkModel.embedding.cosine_distance(query_vector).label("distance")
            ).join(DocumentModel, DocumentChunkModel.document_id == DocumentModel.id)

            if document_id:
                stmt = stmt.where(DocumentChunkModel.document_id == document_id)

            stmt = stmt.order_by("distance").limit(top_k)
            result = await session.execute(stmt)
            rows = result.all()

            results = []
            for chunk, filename, distance in rows:
                sim_score = float(1.0 - distance) if distance is not None else 0.0
                results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": filename,
                    "page_number": chunk.page_number or 1,
                    "content": chunk.content,
                    "metadata": chunk.metadata_json or {},
                    "score": max(0.0, min(1.0, sim_score)),
                    "search_type": "vector"
                })
            return results

        else:
            # Fallback for SQLite / test in-memory databases
            stmt = select(DocumentChunkModel, DocumentModel.filename).join(
                DocumentModel, DocumentChunkModel.document_id == DocumentModel.id
            )
            if document_id:
                stmt = stmt.where(DocumentChunkModel.document_id == document_id)

            result = await session.execute(stmt)
            rows = result.all()

            scored = []
            for chunk, filename in rows:
                chunk_vec = chunk.embedding
                if chunk_vec is None:
                    sim_score = 0.0
                elif isinstance(chunk_vec, list):
                    sim_score = cosine_similarity(query_vector, chunk_vec)
                else:
                    sim_score = 0.0

                scored.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": filename,
                    "page_number": chunk.page_number or 1,
                    "content": chunk.content,
                    "metadata": chunk.metadata_json or {},
                    "score": sim_score,
                    "search_type": "vector"
                })

            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]
