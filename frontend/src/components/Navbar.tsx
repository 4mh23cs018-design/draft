import React from 'react'
import { MessageSquare, FileText, BarChart3, Zap, Wifi, WifiOff } from 'lucide-react'
import { useHealth } from '../hooks/useHealth'

type Page = 'chat' | 'documents' | 'metrics'

interface NavbarProps {
  activePage: Page
  onNavigate: (page: Page) => void
}

export const Navbar: React.FC<NavbarProps> = ({ activePage, onNavigate }) => {
  const { online, health } = useHealth()

  const tabs: { id: Page; label: string; icon: React.ReactNode }[] = [
    { id: 'chat',      label: 'Chat',      icon: <MessageSquare size={15} /> },
    { id: 'documents', label: 'Documents', icon: <FileText size={15} /> },
    { id: 'metrics',   label: 'Metrics',   icon: <BarChart3 size={15} /> },
  ]

  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-surface-950/80 backdrop-blur-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">

        {/* Logo */}
        <div className="flex items-center gap-2.5 select-none">
          <div className="w-8 h-8 rounded-xl bg-brand-500 flex items-center justify-center shadow-glow-sm">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-sm text-white leading-none">RAG Studio</p>
            <p className="text-[10px] text-slate-500 leading-none mt-0.5">
              {health?.version ?? ''}
            </p>
          </div>
        </div>

        {/* Nav Tabs */}
        <nav className="flex items-center gap-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              id={`nav-${tab.id}`}
              onClick={() => onNavigate(tab.id)}
              className={`nav-tab ${activePage === tab.id ? 'nav-tab-active' : 'nav-tab-idle'}`}
            >
              {tab.icon}
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </nav>

        {/* Status Indicator */}
        <div className="flex items-center gap-2 text-xs">
          {online === null ? (
            <span className="text-slate-500 animate-pulse">Connecting…</span>
          ) : online ? (
            <>
              <Wifi size={13} className="text-emerald-400" />
              <span className="text-emerald-400 font-medium hidden sm:inline">
                {health?.embedding_provider ?? 'Online'}
              </span>
            </>
          ) : (
            <>
              <WifiOff size={13} className="text-red-400" />
              <span className="text-red-400 font-medium">Offline</span>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
