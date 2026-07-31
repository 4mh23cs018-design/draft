import React from 'react'
import { UploadArea } from '../components/UploadArea'
import { DocumentList } from '../components/DocumentList'
import { useDocuments } from '../hooks/useDocuments'
import { Database, FileText } from 'lucide-react'

export const DocumentsPage: React.FC = () => {
  const { documents, loading, error, refresh, remove } = useDocuments()

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6 animate-fade-in">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center">
          <Database size={18} className="text-brand-400" />
        </div>
        <div>
          <h1 className="font-bold text-xl text-slate-100">Document Management</h1>
          <p className="text-xs text-slate-500">
            {documents.length > 0
              ? `${documents.length} document${documents.length > 1 ? 's' : ''} · ${documents.reduce((s, d) => s + d.chunk_count, 0)} total chunks indexed`
              : 'Upload documents to build your knowledge base'}
          </p>
        </div>
      </div>

      {/* Upload */}
      <section className="glass p-5">
        <p className="section-title mb-4">Upload Documents</p>
        <UploadArea onUploaded={refresh} />
      </section>

      {/* Library */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <p className="section-title flex items-center gap-1.5">
            <FileText size={11} /> Document Library
          </p>
          {documents.length > 0 && (
            <span className="badge-blue">{documents.length} files</span>
          )}
        </div>
        <DocumentList
          documents={documents}
          loading={loading}
          error={error}
          onDelete={remove}
        />
      </section>
    </div>
  )
}
