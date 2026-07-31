import React from 'react'
import { X, FileText, ChevronRight, Activity, Cpu, Database } from 'lucide-react'
import { RetrievedChunk, ChatMetrics } from '../services/api'

interface DeveloperModePanelProps {
  chunks: RetrievedChunk[]
  metrics?: ChatMetrics
  onClose: () => void
}

const ScoreBar: React.FC<{ value: number; max?: number }> = ({ value, max = 1 }) => {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  return (
    <div className="score-bar w-20">
      <div className="score-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

export const DeveloperModePanel: React.FC<DeveloperModePanelProps> = ({ chunks, metrics, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex" id="dev-mode-panel">
      {/* Backdrop */}
      <div className="flex-1 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Drawer */}
      <aside className="w-full max-w-xl bg-surface-900 border-l border-white/[0.07] h-full overflow-y-auto flex flex-col animate-slide-up">
        {/* Header */}
        <div className="sticky top-0 bg-surface-900/95 backdrop-blur-md border-b border-white/[0.06] px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-amber-500/20 flex items-center justify-center">
              <Activity size={12} className="text-amber-400" />
            </div>
            <p className="font-semibold text-sm text-slate-100">Developer Mode</p>
          </div>
          <button id="close-dev-panel" onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X size={16} />
          </button>
        </div>

        <div className="p-5 flex flex-col gap-6">

          {/* ── Latency & Token Metrics ── */}
          {metrics && (
            <section>
              <p className="section-title mb-3">Performance Metrics</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: 'Retrieval', value: `${metrics.retrieval_latency_ms.toFixed(0)} ms`, icon: <Database size={12} /> },
                  { label: 'LLM',       value: `${metrics.llm_latency_ms.toFixed(0)} ms`,       icon: <Cpu size={12} /> },
                  { label: 'Total',     value: `${metrics.total_latency_ms.toFixed(0)} ms`,      icon: <Activity size={12} /> },
                  { label: 'Precision@K', value: `${(metrics.precision_at_k * 100).toFixed(0)}%`, icon: <ChevronRight size={12} /> },
                ].map(m => (
                  <div key={m.label} className="metric-card animate-fade-in">
                    <div className="flex items-center gap-1.5 text-slate-500">
                      {m.icon}
                      <span className="text-[10px] uppercase tracking-wider">{m.label}</span>
                    </div>
                    <p className="text-lg font-bold text-slate-100 font-mono">{m.value}</p>
                  </div>
                ))}
              </div>

              {/* Token usage */}
              <div className="glass-sm p-3 mt-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">Token Usage</span>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <span className="text-slate-400">Prompt: <span className="text-slate-200">{metrics.token_usage.prompt_tokens}</span></span>
                  <span className="text-slate-400">Completion: <span className="text-slate-200">{metrics.token_usage.completion_tokens}</span></span>
                  <span className="text-slate-400">Total: <span className="text-brand-300">{metrics.token_usage.total_tokens}</span></span>
                </div>
              </div>
            </section>
          )}

          {/* ── Retrieved Chunks ── */}
          <section>
            <p className="section-title mb-3">{chunks.length} Retrieved Chunks</p>
            <div className="flex flex-col gap-3">
              {chunks.map((chunk, i) => {
                const primaryScore = chunk.rerank_score ?? chunk.rrf_score ?? chunk.score ?? 0
                const maxScore = chunk.rerank_score ? 1 : chunk.rrf_score ? 0.05 : 1
                return (
                  <div key={chunk.chunk_id} className="glass-sm p-3 flex flex-col gap-2 animate-fade-in">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-md bg-brand-500/20 text-brand-300 text-[10px] font-bold flex items-center justify-center font-mono">
                          {i + 1}
                        </span>
                        <div>
                          <p className="text-[11px] font-medium text-slate-200 flex items-center gap-1">
                            <FileText size={9} />
                            {chunk.filename}
                          </p>
                          <p className="text-[10px] text-slate-500">Page {chunk.page_number}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <ScoreBar value={primaryScore} max={maxScore} />
                        <span className="text-[10px] font-mono text-brand-300">
                          {primaryScore.toFixed(4)}
                        </span>
                        {chunk.search_type && (
                          <span className={`badge text-[9px] ${chunk.search_type === 'hybrid' ? 'badge-purple' : chunk.search_type === 'vector' ? 'badge-blue' : 'badge-green'}`}>
                            {chunk.search_type}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Scores breakdown */}
                    {(chunk.score !== undefined || chunk.rrf_score !== undefined) && (
                      <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500">
                        {chunk.score !== undefined    && <span>vec: <span className="text-slate-300">{chunk.score.toFixed(4)}</span></span>}
                        {chunk.rrf_score !== undefined && <span>rrf: <span className="text-slate-300">{chunk.rrf_score.toFixed(5)}</span></span>}
                        {chunk.rerank_score !== undefined && <span>rerank: <span className="text-slate-300">{chunk.rerank_score.toFixed(4)}</span></span>}
                      </div>
                    )}

                    {/* Content preview */}
                    <p className="text-[11px] text-slate-400 leading-relaxed border-t border-white/[0.04] pt-2 line-clamp-4 font-mono">
                      {chunk.content}
                    </p>
                  </div>
                )
              })}
            </div>
          </section>

        </div>
      </aside>
    </div>
  )
}
