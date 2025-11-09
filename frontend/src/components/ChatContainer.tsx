import { useState, useEffect, useRef } from 'react'
import { ChatMessage, Message } from './ChatMessage'
import { MessageInput } from './MessageInput'
import styles from './ChatContainer.module.css'

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = (content: string) => {
    // Clear any previous errors
    setError(null)

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Simulate loading state (will be replaced with real API call in Sprint 3)
    setIsLoading(true)

    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: 'This is a simulated response. API integration coming in Sprint 3!',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  return (
    <div className={styles.container}>
      <div className={styles.messagesArea} role="log" aria-label="Chat messages">
        {messages.length === 0 && !isLoading && (
          <div className={styles.emptyState}>
            <p>No messages yet. Start a conversation!</p>
          </div>
        )}
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isLoading && (
          <ChatMessage
            message={{
              id: 'loading',
              role: 'assistant',
              content: '',
              timestamp: new Date(),
            }}
            isLoading={true}
          />
        )}
        <div ref={messagesEndRef} />
      </div>
      {error && (
        <div className={styles.error} role="alert" aria-live="assertive">
          <strong>Error:</strong> {error}
        </div>
      )}
      <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  )
}
