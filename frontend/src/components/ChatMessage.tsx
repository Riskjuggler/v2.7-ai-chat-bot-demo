import styles from './ChatMessage.module.css'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatMessageProps {
  message: Message
  isLoading?: boolean
}

export function ChatMessage({ message, isLoading = false }: ChatMessageProps) {
  const messageClass = `${styles.message} ${styles[message.role]}`

  return (
    <div className={messageClass} role="article" aria-label={`${message.role} message`}>
      <div className={styles.role}>{message.role === 'user' ? 'You' : 'Assistant'}</div>
      <div className={styles.content}>
        {isLoading ? (
          <span className={styles.loading} aria-label="Loading">
            <span className={styles.dot}></span>
            <span className={styles.dot}></span>
            <span className={styles.dot}></span>
          </span>
        ) : (
          message.content
        )}
      </div>
      <div className={styles.timestamp} aria-label="Message timestamp">
        {message.timestamp.toLocaleTimeString()}
      </div>
    </div>
  )
}
