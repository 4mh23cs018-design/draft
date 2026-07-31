import React, { useState } from 'react'
import { Trash2, FileText, FileType, Calendar, Layers, ChevronRight, Loader2, AlertTriangle } from 'lucide-react'
import { Document } from '../services/api'

interface DocumentListProps {
  documents: Document[]
  loading: boolean
  error: string | null
  onDelete: (id: string) => Promise<void>
}

const FILE_TYPE_BADGE: Record<string, string> = {
  pdf:  'badge-red',
  docx: 'badge-blue',
  txt:  'badge-green',
  md:   'badge-purple',
  html: 'badge-amber',
  htm:  'badge-amber',
}

const formatBytes = (b: number) =>
  b < 1024 * 1024 ? `${(b / 1024).toFixed(0)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

export const DocumentList: React.FC<DocumentListProps> = ({
  documents, loading, error, onDelete,
}) => {
  const [deleting, setDeleting] = useState<string | null>(null)

  const handleDelete = async (id: string) => {
    setDeleting(id)
    try {
      await onDelete(id)
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="glass-sm p-4 h-16 shimmer rounded-xl" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-sm p-6 flex flex-col items-center gap-3 text-center">
        <AlertTriangle size={28} className="text-amber-400" />
        <p className="text-sm text-slate-300">{error}</p>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="glass-sm p-10 flex flex-col items-center gap-3 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-brand-500/10 flex items-center justify-center">
          <FileText size={24} className="text-brand-400" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-200">No documents yet</p>
          <p className="text-xs text-slate-500 mt-1">Upload PDF, DOCX, TXT, MD or HTML files to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2 animate-fade-in">
      {documents.map((doc) => (
        <div
          key={doc.id}
          id={`doc-${doc.id}`}
          className="glass-sm p-3 sm:p-4 flex items-center gap-4 hover:bg-white/[0.03] transition-colors group"
        >
          {/* File icon */}
          <div className="w-9 h-9 rounded-xl bg-brand-500/10 flex items-center justify-center shrink-0">
            <FileType size={15} className="text-brand-400" />
          </div>

          {/* Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-slate-100 truncate max-w-[280px]">
                {doc.filename}
              </span>
              <span className={FILE_TYPE_BADGE[doc.file_type] ?? 'badge bg-white/10 text-slate-400'}>
                {doc.file_type}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-500">
              <span className="flex items-center gap-1">
                <Layers size={10} /> {doc.chunk_count} chunks
              </span>
              <span className="flex items-center gap-1">
                <FileText size={10} /> {formatBytes(doc.file_size)}
              </span>
              <span className="flex items-center gap-1">
                <Calendar size={10} /> {formatDate(doc.upload_date)}
              </span>
            </div>
          </div>

          {/* Delete */}
          <button
            id={`delete-doc-${doc.id}`}
            onClick={() => handleDelete(doc.id)}
            disabled={deleting === doc.id}
            className="btn-danger shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            {deleting === doc.id
              ? <Loader2 size={12} className="animate-spin" />
              : <Trash2 size={12} />
            }
            {deleting === doc.id ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      ))}
    </div>
  )
}
