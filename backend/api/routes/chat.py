import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.embeddings.factory import get_embedding_service
from backend.retrieval.hybrid_search import HybridSearchEngine
from backend.retrieval.reranker import RerankerFactory
from backend.prompts.builder import PromptBuilder
from backend.llm.openai_service import OpenAIService
from backend.eval.metrics import EvaluationTracker
from backend.core.config import settings
from backend.core.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question text to answer")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Top-k chunks to retrieve")
    document_id: Optional[str] = Field(default=None, description="Optional document filter")

class CitationSource(BaseModel):
    document: str
    page: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[CitationSource]
    metrics: Optional[Dict[str, Any]] = None
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None

@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    POST /chat
    Full RAG pipeline: Query Embedding -> Hybrid Retrieval -> Reranking -> Grounded Prompt -> LLM Completion -> Sources & Metrics.
    """
    total_start = time.perf_counter()
    question = request.question.strip()
    top_k = request.top_k or settings.TOP_K

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question parameter cannot be empty."
        )

    # Step 1: Embed Query & Retrieve Chunks
    retrieval_start = time.perf_counter()
    embedder = get_embedding_service()
    query_vector = await embedder.embed_text(question)

    # Hybrid Retrieval (Vector + Keyword Search)
    hybrid_chunks = await HybridSearchEngine.search(
        session=db,
        query=question,
        query_vector=query_vector,
        top_k=top_k * 2,  # Fetch candidate pool for reranker
        document_id=request.document_id
    )

    # Reranking
    reranker = RerankerFactory.get_reranker()
    final_chunks = await reranker.rerank(question, hybrid_chunks, top_k=top_k)
    retrieval_latency = (time.perf_counter() - retrieval_start) * 1000

    # Step 2: Build Grounded Prompt
    prompt = PromptBuilder.build_prompt(question, final_chunks)

    # Step 3: LLM Generation
    llm_service = OpenAIService()
    answer, llm_metrics = await llm_service.generate_answer(prompt)

    total_latency = (time.perf_counter() - total_start) * 1000

    # Format Citation Sources
    sources_dict = {}
    for c in final_chunks:
        doc_name = c.get("filename", "Unknown")
        page_num = c.get("page_number", 1)
        key = f"{doc_name}_{page_num}"
        if key not in sources_dict:
            sources_dict[key] = {
                "document": doc_name,
                "page": page_num
            }

    sources = [CitationSource(**s) for s in sources_dict.values()]

    # Record Evaluation Metrics
    eval_record = EvaluationTracker.record_query(
        question=question,
        retrieved_chunks=final_chunks,
        retrieval_latency_ms=retrieval_latency,
        llm_latency_ms=llm_metrics["llm_latency_ms"],
        total_latency_ms=total_latency,
        token_usage={
            "prompt_tokens": llm_metrics["prompt_tokens"],
            "completion_tokens": llm_metrics["completion_tokens"],
            "total_tokens": llm_metrics["total_tokens"]
        }
    )

    metrics_summary = {
        "retrieval_latency_ms": round(retrieval_latency, 2),
        "llm_latency_ms": llm_metrics["llm_latency_ms"],
        "total_latency_ms": round(total_latency, 2),
        "token_usage": eval_record["token_usage"],
        "precision_at_k": eval_record["precision_at_k"]
    }

    return ChatResponse(
        answer=answer,
        sources=sources,
        metrics=metrics_summary,
        retrieved_chunks=final_chunks
    )

@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    POST /chat/stream
    Streaming RAG response endpoint producing Server-Sent Events (SSE).
    """
    question = request.question.strip()
    top_k = request.top_k or settings.TOP_K

    embedder = get_embedding_service()
    query_vector = await embedder.embed_text(question)

    hybrid_chunks = await HybridSearchEngine.search(
        session=db,
        query=question,
        query_vector=query_vector,
        top_k=top_k * 2,
        document_id=request.document_id
    )

    reranker = RerankerFactory.get_reranker()
    final_chunks = await reranker.rerank(question, hybrid_chunks, top_k=top_k)
    prompt = PromptBuilder.build_prompt(question, final_chunks)

    llm_service = OpenAIService()

    async def event_generator():
        async for token in llm_service.stream_answer(prompt):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
