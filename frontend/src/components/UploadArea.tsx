import React, { useCallback, useState } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, X, Loader2 } from 'lucide-react'
import { uploadDocument } from '../services/api'

const ALLOWED_EXTS = ['.pdf', '.docx', '.txt', '.md', '.html', '.htm']
const MAX_MB = 25

interface UploadAreaProps {
  onUploaded: () => void
}

interface UploadState {
  file: File
  status: 'pending' | 'uploading' | 'done' | 'error'
  progress: number
  error?: string
  chunkCount?: number
}

export const UploadArea: React.FC<UploadAreaProps> = ({ onUploaded }) => {
  const [dragging, setDragging] = useState(false)
  const [uploads, setUploads]   = useState<UploadState[]>([])

  const validateFile = (f: File): string | null => {
    const ext = '.' + (f.name.split('.').pop() ?? '').toLowerCase()
    if (!ALLOWED_EXTS.includes(ext)) return `Unsupported format "${ext}"`
    if (f.size > MAX_MB * 1024 * 1024) return `File exceeds ${MAX_MB} MB limit`
    return null
  }

  const processFiles = useCallback(async (files: File[]) => {
    const newUploads: UploadState[] = files.map(f => ({
      file: f,
      status: validateFile(f) ? 'error' : 'pending',
      progress: 0,
      error: validateFile(f) || undefined,
    }))
    setUploads(prev => [...newUploads, ...prev])

    for (let i = 0; i < newUploads.length; i++) {
      if (newUploads[i].status === 'error') continue

      setUploads(prev => prev.map((u, idx) =>
        u.file === newUploads[i].file ? { ...u, status: 'uploading', progress: 30 } : u
      ))

      try {
        const result = await uploadDocument(newUploads[i].file)
        setUploads(prev => prev.map((u) =>
          u.file === newUploads[i].file
            ? { ...u, status: 'done', progress: 100, chunkCount: result.chunk_count }
            : u
        ))
        onUploaded()
      } catch (e: any) {
        const msg = e?.response?.data?.detail ?? 'Upload failed'
        setUploads(prev => prev.map((u) =>
          u.file === newUploads[i].file ? { ...u, status: 'error', error: msg } : u
        ))
      }
    }
  }, [onUploaded])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    processFiles(Array.from(e.dataTransfer.files))
  }, [processFiles])

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) processFiles(Array.from(e.target.files))
    e.target.value = ''
  }

  const dismiss = (file: File) =>
    setUploads(prev => prev.filter(u => u.file !== file))

  const formatSize = (bytes: number) =>
    bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`

  return (
    <div className="flex flex-col gap-4">
      {/* Drop Zone */}
      <label
        id="upload-dropzone"
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`
          relative flex flex-col items-center justify-center gap-3 p-10 rounded-2xl border-2 border-dashed
          cursor-pointer transition-all duration-300 group
          ${dragging
            ? 'border-brand-400 bg-brand-500/10 shadow-glow-sm scale-[1.01]'
            : 'border-white/10 hover:border-brand-500/50 hover:bg-brand-500/5'
          }
        `}
      >
        <input
          id="file-input"
          type="file"
          className="sr-only"
          multiple
          accept={ALLOWED_EXTS.join(',')}
          onChange={onInputChange}
        />

        <div className={`
          w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300
          ${dragging ? 'bg-brand-500/30 shadow-glow-sm' : 'bg-brand-500/10 group-hover:bg-brand-500/20'}
        `}>
          <Upload size={24} className="text-brand-400" />
        </div>

        <div className="text-center">
          <p className="font-semibold text-sm text-slate-200">
            {dragging ? 'Drop files here' : 'Drag & drop files or click to browse'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            PDF, DOCX, TXT, MD, HTML &bull; Max {MAX_MB} MB
          </p>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap justify-center">
          {['.pdf', '.docx', '.txt', '.md', '.html'].map(ext => (
            <span key={ext} className="badge-blue text-[10px] font-mono">{ext}</span>
          ))}
        </div>
      </label>

      {/* Upload progress list */}
      {uploads.length > 0 && (
        <div className="flex flex-col gap-2 animate-fade-in">
          {uploads.map((u, i) => (
            <div key={i} className="glass-sm p-3 flex items-center gap-3">
              {/* Icon */}
              <div className="shrink-0">
                {u.status === 'uploading' && <Loader2 size={16} className="text-brand-400 animate-spin" />}
                {u.status === 'done'      && <CheckCircle size={16} className="text-emerald-400" />}
                {u.status === 'error'     && <AlertCircle size={16} className="text-red-400" />}
                {u.status === 'pending'   && <FileText    size={16} className="text-slate-400" />}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-200 truncate">{u.file.name}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-slate-500">{formatSize(u.file.size)}</span>
                  {u.status === 'done' && u.chunkCount !== undefined && (
                    <span className="text-[10px] text-emerald-400">{u.chunkCount} chunks indexed</span>
                  )}
                  {u.status === 'error' && (
                    <span className="text-[10px] text-red-400">{u.error}</span>
                  )}
                  {u.status === 'uploading' && (
                    <span className="text-[10px] text-brand-400 animate-pulse">Processing…</span>
                  )}
                </div>
                {u.status === 'uploading' && (
                  <div className="score-bar mt-1.5">
                    <div className="score-fill animate-pulse-slow" style={{ width: `${u.progress}%` }} />
                  </div>
                )}
              </div>

              {/* Dismiss */}
              {(u.status === 'done' || u.status === 'error') && (
                <button onClick={() => dismiss(u.file)} className="text-slate-500 hover:text-slate-300 transition-colors">
                  <X size={13} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
