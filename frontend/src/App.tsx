import React, { useState, useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { ChatPage } from './pages/ChatPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { MetricsPage } from './pages/MetricsPage'
import { listDocuments } from './services/api'

type Page = 'chat' | 'documents' | 'metrics'

export default function App() {
  const [page, setPage]           = useState<Page>('chat')
  const [docCount, setDocCount]   = useState(0)

  // Keep document count in sync for chat page awareness
  useEffect(() => {
    const refresh = async () => {
      try {
        const docs = await listDocuments()
        setDocCount(docs.length)
      } catch { /* backend may not be ready */ }
    }
    refresh()

    // Refresh when user navigates back to chat
    if (page === 'chat') refresh()
  }, [page])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar activePage={page} onNavigate={setPage} />

      <main className={`flex-1 min-h-0 ${page === 'chat' ? 'overflow-hidden' : 'overflow-y-auto'}`}>
        {page === 'chat' ? (
          <div className="h-full flex flex-col">
            <ChatPage documentCount={docCount} />
          </div>
        ) : page === 'documents' ? (
          <div className="px-4 sm:px-6 py-8">
            <DocumentsPage />
          </div>
        ) : (
          <div className="px-4 sm:px-6 py-8">
            <MetricsPage />
          </div>
        )}
      </main>
    </div>
  )
}
