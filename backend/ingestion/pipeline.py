"""
Full document ingestion pipeline coordinator.
Orchestrates: extraction → cleaning → chunking → embedding → database storage.
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ingestion.extractors import DocumentExtractor
from backend.ingestion.cleaner import TextCleaner
from backend.ingestion.chunker import RecursiveChunker
from backend.embeddings.base import BaseEmbeddingService
from backend.core.config import settings
from backend.core.logging import logger


class IngestionPipeline:
    """Coordinates the end-to-end document ingestion flow."""

    def __init__(
        self,
        embedding_service: BaseEmbeddingService,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.embedder = embedding_service
        self.chunker = RecursiveChunker(
            chunk_size=chunk_size or settings.CHUNK_SIZE,
            chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP
        )

    async def process(self, filename: str, contents: bytes) -> Dict[str, Any]:
        """
        Runs the full ingestion pipeline and returns chunks with embeddings.

        Returns:
            dict with "cleaned_pages", "chunks", "embeddings"
        """
        # Step 1: Extract text by page
        logger.info(f"Extracting text from '{filename}'")
        extracted = DocumentExtractor.extract(filename, contents)

        # Step 2: Clean each page
        cleaned_pages = []
        for page in extracted:
            cleaned = TextCleaner.clean(page["text"])
            if cleaned:
                cleaned_pages.append({
                    "page_number": page["page_number"],
                    "text": cleaned
                })

        if not cleaned_pages:
            raise ValueError("No readable text found in document after cleaning.")

        # Step 3: Chunk pages
        logger.info(f"Chunking '{filename}' ({len(cleaned_pages)} pages)")
        chunks = self.chunker.chunk_pages(cleaned_pages)

        if not chunks:
            raise ValueError("Chunking produced no output for document.")

        # Step 4: Embed chunks
        logger.info(f"Embedding {len(chunks)} chunks for '{filename}'")
        texts = [c["content"] for c in chunks]
        embeddings = await self.embedder.embed_documents(texts)

        return {
            "cleaned_pages": cleaned_pages,
            "chunks": chunks,
            "embeddings": embeddings
        }
