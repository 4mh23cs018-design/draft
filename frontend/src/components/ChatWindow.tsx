import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
  Send, Sparkles, BookOpen, Code2, Sliders, Loader2, RotateCcw, User, Bot,
} from 'lucide-react'
import { chat, ChatResponse, CitationSource, RetrievedChunk, ChatMetrics } from '../services/api'
import { DeveloperModePanel } from './DeveloperModePanel'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: CitationSource[]
  chunks?: RetrievedChunk[]
  metrics?: ChatMetrics
  loading?: boolean
}

interface ChatWindowProps {
  documentCount: number
}

const TypingDots: React.FC = () => (
  <div className="flex items-center gap-1 py-1">
    <span className="dot" />
    <span className="dot" />
    <span className="dot" />
  </div>
)

const CitationTag: React.FC<{ source: CitationSource }> = ({ source }) => (
  <span className="citation" title={`${source.document}, page ${source.page}`}>
    {source.document.length > 28 ? source.document.slice(0, 25) + '…' : source.document}
    <span className="opacity-60">p.{source.page}</span>
  </span>
)

export const ChatWindow: React.FC<ChatWindowProps> = ({ documentCount }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput]       = useState('')
  const [topK, setTopK]         = useState(5)
  const [loading, setLoading]   = useState(false)
  const [devMode, setDevMode]   = useState(false)
  const [inspectMsg, setInspectMsg] = useState<Message | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async () => {
    const question = input.trim()
    if (!question || loading) return

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: question }
    const assistantMsg: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: '', loading: true }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setInput('')
    setLoading(true)

    try {
      const response: ChatResponse = await chat(question, topK)
      setMessages(prev => prev.map(m =>
        m.id === assistantMsg.id
          ? { ...m, content: response.answer, sources: response.sources, chunks: response.retrieved_chunks, metrics: response.metrics, loading: false }
          : m
      ))
    } catch (e: any) {
      const errMsg = e?.response?.data?.detail ?? 'An error occurred. Please try again.'
      setMessages(prev => prev.map(m =>
        m.id === assistantMsg.id ? { ...m, content: errMsg, loading: false } : m
      ))
    } finally {
      setLoading(false)
    }
  }, [input, loading, topK])

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const onTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
  }

  const clearChat = () => setMessages([])

  const suggestedQuestions = [
    'Summarize the key points from the uploaded documents.',
    'What are the main conclusions?',
    'List all important definitions mentioned.',
  ]

  return (
    <div className="flex flex-col h-full min-h-0 relative">
      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-white/[0.06] bg-surface-950/60">
        <div className="flex items-center gap-3">
          {/* Top-K Selector */}
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Sliders size={12} />
            <span>Top-K:</span>
            <select
              id="top-k-select"
              value={topK}
              onChange={e => setTopK(Number(e.target.value))}
              className="bg-surface-800 border border-white/[0.08] rounded-lg px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-brand-500/50"
            >
              {[3, 5, 8, 10, 15].map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Dev Mode Toggle */}
          <button
            id="dev-mode-toggle"
            onClick={() => setDevMode(!devMode)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all duration-200 ${
              devMode
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.05]'
            }`}
          >
            <Code2 size={12} />
            <span className="hidden sm:inline">Dev Mode</span>
          </button>

          {messages.length > 0 && (
            <button id="clear-chat" onClick={clearChat} className="btn-secondary py-1 text-xs px-2.5">
              <RotateCcw size={11} /> Clear
            </button>
          )}
        </div>
      </div>

      {/* ── Messages Area ── */}
      <div className="flex-1 overflow-y-auto px-4 py-5 flex flex-col gap-5 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-6 animate-fade-in">
            {/* Welcome */}
            <div className="text-center">
              <div className="w-16 h-16 rounded-3xl bg-brand-500/20 border border-brand-500/30 flex items-center justify-center mx-auto mb-4 shadow-glow-sm">
                <Sparkles size={26} className="text-brand-400" />
              </div>
              <h2 className="text-xl font-bold text-slate-100">Ask your documents</h2>
              <p className="text-sm text-slate-500 mt-2 max-w-sm">
                {documentCount > 0
                  ? `${documentCount} document${documentCount > 1 ? 's' : ''} indexed — ask anything`
                  : 'Upload documents first to start asking questions'}
              </p>
            </div>

            {/* Suggested questions */}
            {documentCount > 0 && (
              <div className="w-full max-w-md flex flex-col gap-2">
                <p className="section-title text-center mb-1">Try asking</p>
                {suggestedQuestions.map(q => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); textareaRef.current?.focus() }}
                    className="text-left px-4 py-2.5 rounded-xl border border-white/[0.06] bg-surface-900/40
                               text-xs text-slate-300 hover:bg-brand-500/10 hover:border-brand-500/30
                               transition-all duration-200"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`flex gap-3 animate-slide-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              {/* Avatar */}
              <div className={`w-7 h-7 rounded-xl shrink-0 flex items-center justify-center mt-0.5 ${
                msg.role === 'user' ? 'bg-brand-500' : 'bg-surface-800 border border-white/[0.08]'
              }`}>
                {msg.role === 'user' ? <User size={13} className="text-white" /> : <Bot size={13} className="text-brand-400" />}
              </div>

              <div className="flex flex-col gap-2 min-w-0 max-w-[85%]">
                {/* Bubble */}
                <div className={msg.role === 'user' ? 'bubble-user' : 'bubble-ai'}>
                  {msg.loading ? <TypingDots /> : msg.content}
                </div>

                {/* Sources */}
                {!msg.loading && msg.sources && msg.sources.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap px-1">
                    <BookOpen size={10} className="text-slate-500 shrink-0" />
                    {msg.sources.map((s, i) => <CitationTag key={i} source={s} />)}
                  </div>
                )}

                {/* Metrics row + dev inspect */}
                {!msg.loading && msg.metrics && (
                  <div className="flex items-center gap-3 px-1 flex-wrap">
                    <span className="text-[10px] text-slate-600 font-mono">
                      {msg.metrics.total_latency_ms.toFixed(0)}ms · {msg.metrics.token_usage.total_tokens} tokens
                    </span>
                    {devMode && msg.chunks && (
                      <button
                        onClick={() => setInspectMsg(msg)}
                        className="text-[10px] text-amber-400 hover:text-amber-300 transition-colors font-mono underline underline-offset-2"
                      >
                        Inspect {msg.chunks.length} chunks →
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input Box ── */}
      <div className="px-4 pb-4 pt-2 border-t border-white/[0.06] bg-surface-950/60">
        <div className="flex items-end gap-2.5">
          <textarea
            id="chat-input"
            ref={textareaRef}
            value={input}
            onChange={onTextareaChange}
            onKeyDown={onKeyDown}
            placeholder={documentCount > 0 ? 'Ask a question about your documents…' : 'Upload documents first…'}
            disabled={documentCount === 0 || loading}
            rows={1}
            className="input-field resize-none leading-relaxed flex-1"
            style={{ maxHeight: '160px' }}
          />
          <button
            id="send-chat-btn"
            onClick={handleSend}
            disabled={!input.trim() || loading || documentCount === 0}
            className="btn-primary shrink-0 h-11 w-11 p-0 flex items-center justify-center"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={15} />}
          </button>
        </div>
        <p className="text-[10px] text-slate-600 mt-1.5 px-1">Enter to send · Shift+Enter for newline</p>
      </div>

      {/* Developer Mode Panel */}
      {devMode && inspectMsg && (
        <DeveloperModePanel
          chunks={inspectMsg.chunks ?? []}
          metrics={inspectMsg.metrics}
          onClose={() => setInspectMsg(null)}
        />
      )}
    </div>
  )
}
