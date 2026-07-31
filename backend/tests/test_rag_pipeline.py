import pytest
import io
from backend.ingestion.extractors import DocumentExtractor
from backend.ingestion.cleaner import TextCleaner
from backend.ingestion.chunker import RecursiveChunker
from backend.embeddings.mock_embedder import MockEmbeddingService
from backend.prompts.builder import PromptBuilder
from backend.retrieval.vector_search import cosine_similarity

@pytest.mark.asyncio
async def test_text_cleaner():
    raw = "Hello   World!\r\n\r\n\n\nThis is a   test.\x00"
    cleaned = TextCleaner.clean(raw)
    assert "Hello World!" in cleaned
    assert "This is a test." in cleaned
    assert "\x00" not in cleaned

@pytest.mark.asyncio
async def test_extractors():
    txt_content = b"Header Text\n\nThis is sample document content."
    res = DocumentExtractor.extract("sample.txt", txt_content)
    assert len(res) == 1
    assert "sample document content" in res[0]["text"]

    html_content = b"<html><body><h1>Title</h1><p>Paragraph text</p></body></html>"
    res_html = DocumentExtractor.extract("index.html", html_content)
    assert "Title" in res_html[0]["text"]
    assert "Paragraph text" in res_html[0]["text"]

@pytest.mark.asyncio
async def test_chunker():
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
    pages = [
        {"page_number": 1, "text": "Sentence one is long enough. " * 5},
        {"page_number": 2, "text": "Page two text goes here. " * 5}
    ]
    chunks = chunker.chunk_pages(pages)
    assert len(chunks) > 0
    assert chunks[0]["page_number"] == 1
    assert chunks[-1]["page_number"] in [1, 2]

@pytest.mark.asyncio
async def test_mock_embedder():
    embedder = MockEmbeddingService(dimension=1536)
    vec1 = await embedder.embed_text("RAG architecture")
    vec2 = await embedder.embed_text("RAG architecture")
    vec3 = await embedder.embed_text("Unrelated topic")

    assert len(vec1) == 1536
    assert vec1 == vec2  # Deterministic
    sim_same = cosine_similarity(vec1, vec2)
    sim_diff = cosine_similarity(vec1, vec3)
    assert pytest.approx(sim_same, 0.0001) == 1.0
    assert sim_diff < 0.99

@pytest.mark.asyncio
async def test_prompt_builder():
    chunks = [
        {
            "filename": "guide.pdf",
            "page_number": 3,
            "content": "RAG improves LLM answers using document retrieval."
        }
    ]
    prompt = PromptBuilder.build_prompt("What is RAG?", chunks)
    assert "Answer ONLY from the supplied context." in prompt
    assert "Source: guide.pdf (Page 3)" in prompt
    assert "RAG improves LLM answers using document retrieval." in prompt
    assert "Question:\nWhat is RAG?" in prompt

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data

@pytest.mark.asyncio
async def test_document_lifecycle_and_chat(async_client):
    # 1. Upload document
    sample_text = b"Retrieval-Augmented Generation (RAG) is a technique for enhancing LLM outputs with external factual documents. Page 1 content."
    files = {"file": ("manual.txt", io.BytesIO(sample_text), "text/plain")}
    
    upload_res = await async_client.post("/documents", files=files)
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["document_id"]
    assert doc_data["filename"] == "manual.txt"
    assert doc_data["chunk_count"] > 0

    # 2. List documents
    list_res = await async_client.get("/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["id"] == doc_id for d in docs)

    # 3. Chat query grounded in document
    chat_payload = {
        "question": "What is Retrieval-Augmented Generation?",
        "top_k": 3
    }
    chat_res = await async_client.post("/chat", json=chat_payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "answer" in chat_data
    assert "sources" in chat_data
    assert len(chat_data["sources"]) > 0
    assert chat_data["sources"][0]["document"] == "manual.txt"

    # 4. Evaluation metrics endpoint
    eval_res = await async_client.get("/eval/metrics")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["total_queries"] >= 1

    # 5. Delete document
    del_res = await async_client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify document list is now empty
    list_after = await async_client.get("/documents")
    assert not any(d["id"] == doc_id for d in list_after.json())
