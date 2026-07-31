import React, { useEffect, useState } from 'react'
import { BarChart3, Activity, Cpu, Database, Zap, MessageSquare, RefreshCw, Loader2 } from 'lucide-react'
import { getEvalMetrics, EvalMetrics } from '../services/api'

const StatCard: React.FC<{ label: string; value: string | number; sub?: string; icon: React.ReactNode; accent?: string }> = ({
  label, value, sub, icon, accent = 'text-brand-400'
}) => (
  <div className="metric-card animate-fade-in">
    <div className={`flex items-center gap-1.5 ${accent} text-[10px] uppercase tracking-widest font-semibold`}>
      {icon}
      {label}
    </div>
    <p className="text-2xl font-bold text-slate-100 font-mono mt-1">{value}</p>
    {sub && <p className="text-[10px] text-slate-500 mt-0.5">{sub}</p>}
  </div>
)

export const MetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<EvalMetrics | null>(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      setMetrics(await getEvalMetrics())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={24} className="text-brand-400 animate-spin" />
      </div>
    )
  }

  const formatMs = (ms: number) => ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms.toFixed(0)}ms`

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-lg text-slate-100">RAG Evaluation Metrics</h2>
          <p className="text-xs text-slate-500 mt-0.5">Performance analytics across all queries</p>
        </div>
        <button id="refresh-metrics" onClick={load} disabled={loading} className="btn-secondary py-1.5 text-xs">
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard
          label="Total Queries"   value={metrics.total_queries}
          icon={<MessageSquare size={11} />} accent="text-brand-400"
        />
        <StatCard
          label="Avg Retrieval"   value={formatMs(metrics.avg_retrieval_latency_ms)}
          sub="vector + keyword search"
          icon={<Database size={11} />} accent="text-blue-400"
        />
        <StatCard
          label="Avg LLM"         value={formatMs(metrics.avg_llm_latency_ms)}
          sub="generation latency"
          icon={<Cpu size={11} />} accent="text-purple-400"
        />
        <StatCard
          label="Avg Total"       value={formatMs(metrics.avg_total_latency_ms)}
          sub="end-to-end"
          icon={<Activity size={11} />} accent="text-emerald-400"
        />
        <StatCard
          label="Avg Precision@K" value={`${(metrics.avg_precision_at_k * 100).toFixed(0)}%`}
          sub="relevant retrieved chunks"
          icon={<BarChart3 size={11} />} accent="text-amber-400"
        />
        <StatCard
          label="Total Tokens"    value={metrics.total_tokens_consumed.toLocaleString()}
          sub="all-time token spend"
          icon={<Zap size={11} />} accent="text-red-400"
        />
      </div>

      {/* Recent Queries Table */}
      {metrics.recent_queries.length > 0 && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-white/[0.05]">
            <p className="text-sm font-semibold text-slate-200">Recent Queries</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.04]">
                  {['Question', 'Retrieval', 'LLM', 'Total', 'Prec@K', 'Tokens'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-slate-500 font-semibold uppercase tracking-wider text-[10px] whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.recent_queries.map((q, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 text-slate-300 max-w-[200px] truncate" title={q.question}>
                      {q.question}
                    </td>
                    <td className="px-4 py-3 font-mono text-blue-300">{formatMs(q.retrieval_latency_ms)}</td>
                    <td className="px-4 py-3 font-mono text-purple-300">{formatMs(q.llm_latency_ms)}</td>
                    <td className="px-4 py-3 font-mono text-emerald-300">{formatMs(q.total_latency_ms)}</td>
                    <td className="px-4 py-3 font-mono text-amber-300">{(q.precision_at_k * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3 font-mono text-slate-400">{q.token_usage?.total_tokens ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {metrics.total_queries === 0 && (
        <div className="glass-sm p-10 flex flex-col items-center gap-3 text-center">
          <BarChart3 size={28} className="text-brand-400" />
          <p className="text-sm text-slate-400">No queries recorded yet. Start chatting to see metrics.</p>
        </div>
      )}
    </div>
  )
}
