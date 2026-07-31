import React from 'react'
import { ChatWindow } from '../components/ChatWindow'

interface ChatPageProps {
  documentCount: number
}

export const ChatPage: React.FC<ChatPageProps> = ({ documentCount }) => {
  return (
    <div className="flex flex-col h-full min-h-0">
      <ChatWindow documentCount={documentCount} />
    </div>
  )
}
