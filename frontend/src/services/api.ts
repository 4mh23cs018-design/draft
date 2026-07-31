import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({ baseURL: BASE })

// ──────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────

export interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  upload_date: string
  chunk_count: number
}

export interface CitationSource {
  document: string
  page: number
}

export interface RetrievedChunk {
  chunk_id: string
  document_id: string
  filename: string
  page_number: number
  content: string
  score?: number
  rrf_score?: number
  rerank_score?: number
  search_type?: string
}

export interface ChatMetrics {
  retrieval_latency_ms: number
  llm_latency_ms: number
  total_latency_ms: number
  token_usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  precision_at_k: number
}

export interface ChatResponse {
  answer: string
  sources: CitationSource[]
  metrics?: ChatMetrics
  retrieved_chunks?: RetrievedChunk[]
}

export interface EvalMetrics {
  total_queries: number
  avg_retrieval_latency_ms: number
  avg_llm_latency_ms: number
  avg_total_latency_ms: number
  avg_precision_at_k: number
  total_tokens_consumed: number
  recent_queries: Array<{
    timestamp: number
    question: string
    chunk_count: number
    precision_at_k: number
    retrieval_latency_ms: number
    llm_latency_ms: number
    total_latency_ms: number
    token_usage: { total_tokens: number }
  }>
}

export interface HealthStatus {
  status: string
  service: string
  version: string
  database: string
  embedding_provider: string
  chunk_size: number
  top_k: number
}

// ──────────────────────────────────────────────
// API Functions
// ──────────────────────────────────────────────

export const uploadDocument = async (file: File): Promise<{ document_id: string; filename: string; chunk_count: number }> => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/documents', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const listDocuments = async (): Promise<Document[]> => {
  const { data } = await api.get('/documents')
  return data
}

export const deleteDocument = async (id: string): Promise<void> => {
  await api.delete(`/documents/${id}`)
}

export const chat = async (question: string, top_k = 5, document_id?: string): Promise<ChatResponse> => {
  const { data } = await api.post('/chat', { question, top_k, document_id })
  return data
}

export const getHealth = async (): Promise<HealthStatus> => {
  const { data } = await api.get('/health')
  return data
}

export const getEvalMetrics = async (): Promise<EvalMetrics> => {
  const { data } = await api.get('/eval/metrics')
  return data
}

export const streamChat = (
  question: string,
  top_k: number,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: Error) => void
) => {
  const ctrl = new AbortController()

  fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k }),
    signal: ctrl.signal,
  }).then(async (res) => {
    if (!res.ok || !res.body) { onError(new Error('Stream failed')); return }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) { onDone(); break }
      const text = decoder.decode(value)
      const lines = text.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6)
          if (chunk === '[DONE]') { onDone(); return }
          onToken(chunk)
        }
      }
    }
  }).catch((e) => { if (e.name !== 'AbortError') onError(e) })

  return () => ctrl.abort()
}
