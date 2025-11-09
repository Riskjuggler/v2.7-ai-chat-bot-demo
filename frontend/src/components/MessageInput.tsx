import { useState, KeyboardEvent } from 'react'
import styles from './MessageInput.module.css'

export interface MessageInputProps {
  onSendMessage: (content: string) => void
  disabled?: boolean
}

export function MessageInput({ onSendMessage, disabled = false }: MessageInputProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    const trimmedInput = input.trim()
    if (trimmedInput && !disabled) {
      onSendMessage(trimmedInput)
      setInput('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={styles.inputContainer}>
      <textarea
        className={styles.textarea}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="Type your message..."
        disabled={disabled}
        aria-label="Message input"
        rows={3}
      />
      <button
        className={styles.sendButton}
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        aria-label="Send message"
      >
        Send
      </button>
    </div>
  )
}
