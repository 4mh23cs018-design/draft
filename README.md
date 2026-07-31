# RAG Studio 🚀

> A **production-ready Retrieval-Augmented Generation (RAG)** system — upload any document, ask natural language questions, and receive grounded answers with citations.

---

## Architecture

```
┌──────────────────────┐         ┌────────────────────────────────────────────────────────────┐
│   React + Vite + TS  │  REST   │                  FastAPI Backend                           │
│      Frontend        │ ──────► │  /documents   /chat   /health   /eval/metrics             │
│   (Port 5173)        │         └─────────────────────────┬──────────────────────────────────┘
└──────────────────────┘                                   │
                                          ┌────────────────▼────────────────┐
                                          │        Ingestion Pipeline        │
                                          │ Extract → Clean → Chunk → Embed  │
                                          └────────────────┬────────────────┘
                                                           │
                                          ┌────────────────▼────────────────┐
                                          │   PostgreSQL + pgvector (pg16)   │
                                          │  Documents • Chunks • Embeddings │
                                          └────────────────┬────────────────┘
                                                           │
                                          ┌────────────────▼────────────────┐
                                          │      Hybrid Retrieval Engine     │
                                          │  Vector Search + Keyword (BM25)  │
                                          │       Fused via RRF Ranking       │
                                          └────────────────┬────────────────┘
                                                           │
                                          ┌────────────────▼────────────────┐
                                          │  Pluggable Reranker              │
                                          │  Cohere | BGE | Jina | Score     │
                                          └────────────────┬────────────────┘
                                                           │
                                          ┌────────────────▼────────────────┐
                                          │  Prompt Builder + OpenAI GPT     │
                                          │  Grounded Answer + Citations     │
                                          └─────────────────────────────────┘
```

---

## Features

| Feature | Status |
|---|---|
| PDF / DOCX / TXT / MD / HTML ingestion | ✅ |
| Recursive text chunking (configurable size/overlap) | ✅ |
| OpenAI `text-embedding-3-small` embeddings | ✅ |
| Mock embedding service (offline/test) | ✅ |
| Cosine vector similarity search via pgvector | ✅ |
| BM25 keyword search | ✅ |
| Hybrid retrieval with Reciprocal Rank Fusion | ✅ |
| Pluggable reranker (Cohere / BGE / Jina / Score) | ✅ |
| Grounded prompt builder with source citations | ✅ |
| Streaming chat responses (SSE) | ✅ |
| Evaluation metrics (latency, tokens, Precision@K) | ✅ |
| Structured JSON logging | ✅ |
| File validation (size, extension, sanitization) | ✅ |
| Docker + docker-compose one-command startup | ✅ |
| React + TypeScript + Tailwind dark-mode UI | ✅ |
| Developer mode (chunk inspection, score breakdown) | ✅ |
| Full unit + integration test suite | ✅ |

---

## Quick Start

### Option A – Docker (Recommended)

**Prerequisites:** Docker + Docker Compose

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

# 2. Start everything
docker compose up --build

# API at: http://localhost:8000
# Health: http://localhost:8000/health
```

---

### Option B – Local Development

**Prerequisites:** Python 3.12+, Node 18+, PostgreSQL with pgvector

#### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Set DATABASE_URL and OPENAI_API_KEY in .env

# Run tests
python -m pytest backend/tests/ -v

# Start backend
python -m uvicorn backend.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
# UI at: http://localhost:5173
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key (leave blank for mock/offline mode) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async SQLAlchemy database URL |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model name |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI chat completion model |
| `CHUNK_SIZE` | `500` | Maximum characters per text chunk |
| `CHUNK_OVERLAP` | `50` | Character overlap between consecutive chunks |
| `TOP_K` | `5` | Default number of chunks to retrieve |
| `HYBRID_SEARCH_ENABLED` | `true` | Enable hybrid vector+keyword retrieval |
| `VECTOR_WEIGHT` | `0.6` | Weight for vector search in RRF fusion |
| `KEYWORD_WEIGHT` | `0.4` | Weight for keyword search in RRF fusion |
| `RERANK_ENABLED` | `false` | Enable document reranking stage |
| `RERANK_PROVIDER` | `score` | Reranker: `score`, `cohere`, `bge`, `jina` |
| `COHERE_API_KEY` | *(optional)* | Cohere API key for Cohere Rerank |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum upload file size in megabytes |

---

## API Reference

### Upload Document

```http
POST /documents
Content-Type: multipart/form-data

file: <binary>
```

```json
{
  "document_id": "abc-123",
  "filename": "report.pdf",
  "chunk_count": 47,
  "upload_date": "2025-01-01T12:00:00"
}
```

---

### List Documents

```http
GET /documents
```

---

### Delete Document

```http
DELETE /documents/{id}
```

Deletes the document and **all associated embeddings** from the vector store.

---

### Chat (RAG Query)

```http
POST /chat
Content-Type: application/json

{
  "question": "What are the key findings?",
  "top_k": 5
}
```

```json
{
  "answer": "The key findings are... [1]",
  "sources": [
    { "document": "report.pdf", "page": 3 }
  ],
  "metrics": {
    "retrieval_latency_ms": 42,
    "llm_latency_ms": 820,
    "total_latency_ms": 865,
    "token_usage": { "prompt_tokens": 512, "completion_tokens": 148, "total_tokens": 660 },
    "precision_at_k": 0.8
  }
}
```

---

### Streaming Chat

```http
POST /chat/stream
Content-Type: application/json

{ "question": "...", "top_k": 5 }
```

Returns `text/event-stream` (SSE).

---

### Health Check

```http
GET /health
```

---

### Evaluation Metrics

```http
GET /eval/metrics
```

---

## Project Structure

```
projecter/
├── backend/
│   ├── api/routes/        # FastAPI route handlers
│   ├── core/              # Config, logging, security
│   ├── db/                # SQLAlchemy models & session
│   ├── embeddings/        # Embedding service abstraction
│   ├── eval/              # Retrieval & latency metrics
│   ├── ingestion/         # Extractors, cleaner, chunker, pipeline
│   ├── llm/               # OpenAI LLM service + streaming
│   ├── prompts/           # Grounded prompt builder
│   ├── retrieval/         # Vector, keyword, hybrid search, reranker
│   ├── tests/             # Unit & integration tests
│   └── main.py            # Application entry point
├── frontend/
│   └── src/
│       ├── components/    # Navbar, ChatWindow, UploadArea, etc.
│       ├── hooks/         # useDocuments, useHealth
│       ├── pages/         # ChatPage, DocumentsPage, MetricsPage
│       └── services/      # Typed API client
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Running Tests

```bash
python -m pytest backend/tests/ -v
```

All 7 tests cover: text cleaning, extraction, chunking, embedding, prompt building, health endpoint, and the full document lifecycle + chat integration flow.
