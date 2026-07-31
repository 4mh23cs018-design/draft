import { useState, useEffect, useCallback } from 'react'
import { listDocuments, deleteDocument, Document } from '../services/api'

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const remove = async (id: string) => {
    await deleteDocument(id)
    setDocuments((d) => d.filter((doc) => doc.id !== id))
  }

  return { documents, loading, error, refresh, remove }
}
