import re
import math
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import DocumentChunkModel, DocumentModel

class KeywordSearchEngine:
    """Keyword & BM25 text search engine."""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\w+', text)]

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query_tokens = cls._tokenize(query)
        if not query_tokens:
            return []

        stmt = select(DocumentChunkModel, DocumentModel.filename).join(
            DocumentModel, DocumentChunkModel.document_id == DocumentModel.id
        )
        if document_id:
            stmt = stmt.where(DocumentChunkModel.document_id == document_id)

        result = await session.execute(stmt)
        rows = result.all()

        scored = []
        for chunk, filename in rows:
            content_tokens = cls._tokenize(chunk.content)
            if not content_tokens:
                continue

            # Calculate BM25-style TF score
            doc_len = len(content_tokens)
            score = 0.0
            for qt in set(query_tokens):
                tf = content_tokens.count(qt)
                if tf > 0:
                    score += (tf * (1.5 + 1)) / (tf + 1.5 * (1 - 0.75 + 0.75 * (doc_len / 200.0)))

            if score > 0:
                scored.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": filename,
                    "page_number": chunk.page_number or 1,
                    "content": chunk.content,
                    "metadata": chunk.metadata_json or {},
                    "score": score,
                    "search_type": "keyword"
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
