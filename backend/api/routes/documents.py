import datetime
import uuid
from datetime import timezone
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.db.database import get_db
from backend.db.models import DocumentModel, DocumentChunkModel
from backend.core.security import sanitize_filename, validate_upload_file
from backend.ingestion.extractors import DocumentExtractor
from backend.ingestion.cleaner import TextCleaner
from backend.ingestion.chunker import RecursiveChunker
from backend.embeddings.factory import get_embedding_service
from backend.core.config import settings
from backend.core.logging import logger

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    POST /documents
    Upload, process, chunk, embed, and store document with metadata.
    """
    contents = await file.read()
    filename = sanitize_filename(file.filename or "uploaded_file")
    
    # Security validations
    validate_upload_file(file, contents)

    logger.info(f"Processing uploaded document '{filename}' ({len(contents)} bytes)")

    # Step 1 & 2: Extract text per page
    extracted_pages = DocumentExtractor.extract(filename, contents)

    # Step 3: Clean extracted text
    cleaned_pages = []
    for page in extracted_pages:
        cleaned_text = TextCleaner.clean(page["text"])
        if cleaned_text:
            cleaned_pages.append({
                "page_number": page["page_number"],
                "text": cleaned_text
            })

    if not cleaned_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document contains no readable text after cleaning."
        )

    # Step 4: Chunk text recursively
    chunker = RecursiveChunker(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    raw_chunks = chunker.chunk_pages(cleaned_pages)

    if not raw_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate text chunks from document."
        )

    # Step 5: Generate Embeddings
    embedder = get_embedding_service()
    chunk_texts = [c["content"] for c in raw_chunks]
    embeddings = await embedder.embed_documents(chunk_texts)

    # Step 6 & 7: Store Document and Chunks with metadata in DB
    doc_id = str(uuid.uuid4())
    upload_date = datetime.datetime.now(timezone.utc)
    file_ext = filename.split(".")[-1].lower() if "." in filename else "txt"

    doc_record = DocumentModel(
        id=doc_id,
        filename=filename,
        file_type=file_ext,
        file_size=len(contents),
        upload_date=upload_date,
        chunk_count=len(raw_chunks)
    )
    db.add(doc_record)

    chunk_objects = []
    for idx, (chunk_data, emb) in enumerate(zip(raw_chunks, embeddings)):
        chunk_id = f"{doc_id}_chunk_{idx}"
        metadata = {
            "filename": filename,
            "page_number": chunk_data["page_number"],
            "chunk_id": chunk_id,
            "upload_date": upload_date.isoformat(),
            "source": filename,
            "document_id": doc_id
        }
        chunk_obj = DocumentChunkModel(
            id=chunk_id,
            document_id=doc_id,
            chunk_index=chunk_data["chunk_index"],
            page_number=chunk_data["page_number"],
            content=chunk_data["content"],
            metadata_json=metadata,
            embedding=emb
        )
        chunk_objects.append(chunk_obj)

    db.add_all(chunk_objects)
    await db.commit()
    await db.refresh(doc_record)

    logger.info(f"Successfully ingested document '{filename}' with ID {doc_id} ({len(chunk_objects)} chunks)")

    return {
        "document_id": doc_id,
        "filename": filename,
        "chunk_count": len(chunk_objects),
        "upload_date": upload_date.isoformat()
    }

@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)):
    """
    GET /documents
    List all uploaded documents.
    """
    stmt = select(DocumentModel).order_by(DocumentModel.upload_date.desc())
    result = await db.execute(stmt)
    documents = result.scalars().all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "upload_date": doc.upload_date.isoformat(),
            "chunk_count": doc.chunk_count
        }
        for doc in documents
    ]

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    DELETE /documents/{id}
    Deletes document and cascades deletion of all associated chunks/embeddings.
    """
    stmt = select(DocumentModel).where(DocumentModel.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    await db.delete(doc)
    await db.commit()

    logger.info(f"Deleted document {document_id} and its associated embeddings.")

    return {
        "status": "success",
        "deleted_document_id": document_id
    }
