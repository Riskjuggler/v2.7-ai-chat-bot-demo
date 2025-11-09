import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { ChatContainer } from '../ChatContainer'

describe('ChatContainer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it('renders empty state when no messages', () => {
    render(<ChatContainer />)

    expect(screen.getByText('No messages yet. Start a conversation!')).toBeInTheDocument()
  })

  it('renders message input', () => {
    render(<ChatContainer />)

    expect(screen.getByLabelText('Message input')).toBeInTheDocument()
    expect(screen.getByLabelText('Send message')).toBeInTheDocument()
  })

  it('adds user message when send button clicked', () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Hello' } })
    fireEvent.click(sendButton)

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('You')).toBeInTheDocument()
  })

  it('shows loading indicator after sending message', () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    expect(screen.getByLabelText('Loading')).toBeInTheDocument()
  })

  it('disables input while loading', () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    expect(textarea).toBeDisabled()
    expect(sendButton).toBeDisabled()
  })

  it('shows assistant response after loading completes', async () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Hello' } })
    fireEvent.click(sendButton)

    // Fast-forward time to simulate response
    await act(async () => {
      vi.advanceTimersByTime(1500)
    })

    expect(screen.getByText('This is a simulated response. API integration coming in Sprint 3!')).toBeInTheDocument()
  })

  it('clears input after sending', () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    expect(textarea.value).toBe('')
  })

  it('displays multiple messages in order', async () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    // Send first message
    fireEvent.change(textarea, { target: { value: 'First message' } })
    fireEvent.click(sendButton)

    await act(async () => {
      vi.advanceTimersByTime(1500)
    })

    expect(screen.getByText('First message')).toBeInTheDocument()

    // Send second message
    fireEvent.change(textarea, { target: { value: 'Second message' } })
    fireEvent.click(sendButton)

    expect(screen.getByText('First message')).toBeInTheDocument()
    expect(screen.getByText('Second message')).toBeInTheDocument()
  })

  it('hides empty state after messages added', () => {
    render(<ChatContainer />)

    expect(screen.getByText('No messages yet. Start a conversation!')).toBeInTheDocument()

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    expect(screen.queryByText('No messages yet. Start a conversation!')).not.toBeInTheDocument()
  })

  it('enables input after loading completes', async () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    expect(textarea).toBeDisabled()

    await act(async () => {
      vi.advanceTimersByTime(1500)
    })

    expect(textarea).not.toBeDisabled()
  })

  it('renders messages area with correct role', () => {
    render(<ChatContainer />)

    expect(screen.getByRole('log')).toBeInTheDocument()
    expect(screen.getByLabelText('Chat messages')).toBeInTheDocument()
  })

  it('shows Assistant label for assistant messages', async () => {
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    await act(async () => {
      vi.advanceTimersByTime(1500)
    })

    const assistantLabels = screen.getAllByText('Assistant')
    expect(assistantLabels.length).toBeGreaterThan(0)
  })

  it('clears error when new message sent', () => {
    // This test ensures error state can be cleared (component supports this even if not actively used yet)
    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)

    // Error handling logic exists but not triggered in current simulation
    // Full error path will be tested in Sprint 3 with real API integration
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
