import { useState, useEffect, useRef } from 'react'
import { ChatMessage, Message } from './ChatMessage'
import { MessageInput } from './MessageInput'
import { apiClient, ApiError } from '../services/apiClient'
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

  const handleSendMessage = async (content: string) => {
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

    // Call API to get LLM response
    setIsLoading(true)

    try {
      const response = await apiClient.sendMessage({ message: content })

      // Add assistant response
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      // Handle API errors
      let errorMessage = 'An unexpected error occurred'

      if (err instanceof ApiError) {
        if (err.statusCode === 503) {
          errorMessage = 'LLM service is currently unavailable. Please try again later.'
        } else if (err.statusCode === 408) {
          errorMessage = 'Request timed out. Please try again.'
        } else if (err.statusCode === 422) {
          errorMessage = 'Invalid message. Please check your input.'
        } else {
          errorMessage = err.detail || err.message
        }
      } else if (err instanceof Error) {
        errorMessage = err.message
      }

      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
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
