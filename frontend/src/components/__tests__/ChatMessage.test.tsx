import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatMessage, Message } from '../ChatMessage'

describe('ChatMessage', () => {
  const mockUserMessage: Message = {
    id: '1',
    role: 'user',
    content: 'Hello, this is a test message',
    timestamp: new Date('2025-11-09T14:00:00'),
  }

  const mockAssistantMessage: Message = {
    id: '2',
    role: 'assistant',
    content: 'This is a response',
    timestamp: new Date('2025-11-09T14:01:00'),
  }

  it('renders user message correctly', () => {
    render(<ChatMessage message={mockUserMessage} />)

    expect(screen.getByText('You')).toBeInTheDocument()
    expect(screen.getByText('Hello, this is a test message')).toBeInTheDocument()
    expect(screen.getByLabelText('user message')).toBeInTheDocument()
  })

  it('renders assistant message correctly', () => {
    render(<ChatMessage message={mockAssistantMessage} />)

    expect(screen.getByText('Assistant')).toBeInTheDocument()
    expect(screen.getByText('This is a response')).toBeInTheDocument()
    expect(screen.getByLabelText('assistant message')).toBeInTheDocument()
  })

  it('displays timestamp', () => {
    render(<ChatMessage message={mockUserMessage} />)

    const timestamp = screen.getByLabelText('Message timestamp')
    expect(timestamp).toBeInTheDocument()
    expect(timestamp.textContent).toContain(':')
  })

  it('shows loading state when isLoading is true', () => {
    render(<ChatMessage message={mockAssistantMessage} isLoading={true} />)

    expect(screen.getByLabelText('Loading')).toBeInTheDocument()
    expect(screen.queryByText('This is a response')).not.toBeInTheDocument()
  })

  it('shows message content when isLoading is false', () => {
    render(<ChatMessage message={mockUserMessage} isLoading={false} />)

    expect(screen.getByText('Hello, this is a test message')).toBeInTheDocument()
    expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument()
  })

  it('applies correct CSS class for user role', () => {
    const { container } = render(<ChatMessage message={mockUserMessage} />)

    const messageDiv = container.querySelector('[role="article"]')
    expect(messageDiv?.className).toContain('message')
    expect(messageDiv?.className).toContain('user')
  })

  it('applies correct CSS class for assistant role', () => {
    const { container } = render(<ChatMessage message={mockAssistantMessage} />)

    const messageDiv = container.querySelector('[role="article"]')
    expect(messageDiv?.className).toContain('message')
    expect(messageDiv?.className).toContain('assistant')
  })

  it('renders loading dots when loading', () => {
    const { container } = render(<ChatMessage message={mockAssistantMessage} isLoading={true} />)

    const dots = container.querySelectorAll('[class*="dot"]')
    expect(dots).toHaveLength(3)
  })
})
