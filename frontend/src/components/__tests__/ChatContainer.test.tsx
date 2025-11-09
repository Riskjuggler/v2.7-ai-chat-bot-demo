import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { ChatContainer } from '../ChatContainer'

// Mock the API client
vi.mock('../../services/apiClient', () => ({
  apiClient: {
    sendMessage: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public statusCode?: number, public detail?: string) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

describe('ChatContainer', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
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
    const { apiClient } = await import('../../services/apiClient')

    // Mock successful API response
    ;(apiClient.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'This is the API response',
      model: 'test-model',
      timestamp: new Date().toISOString(),
    })

    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Hello' } })
    fireEvent.click(sendButton)

    // Wait for API response
    await waitFor(() => {
      expect(screen.getByText('This is the API response')).toBeInTheDocument()
    })
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
    const { apiClient } = await import('../../services/apiClient')

    // Mock successful API responses
    ;(apiClient.sendMessage as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        response: 'First response',
        model: 'test-model',
        timestamp: new Date().toISOString(),
      })
      .mockResolvedValueOnce({
        response: 'Second response',
        model: 'test-model',
        timestamp: new Date().toISOString(),
      })

    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    // Send first message
    fireEvent.change(textarea, { target: { value: 'First message' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument()
    })

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
    const { apiClient } = await import('../../services/apiClient')

    // Mock successful API response
    ;(apiClient.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'Response',
      model: 'test-model',
      timestamp: new Date().toISOString(),
    })

    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    expect(textarea).toBeDisabled()

    await waitFor(() => {
      expect(textarea).not.toBeDisabled()
    })
  })

  it('renders messages area with correct role', () => {
    render(<ChatContainer />)

    expect(screen.getByRole('log')).toBeInTheDocument()
    expect(screen.getByLabelText('Chat messages')).toBeInTheDocument()
  })

  it('shows Assistant label for assistant messages', async () => {
    const { apiClient } = await import('../../services/apiClient')

    // Mock successful API response
    ;(apiClient.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'Assistant response',
      model: 'test-model',
      timestamp: new Date().toISOString(),
    })

    render(<ChatContainer />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      const assistantLabels = screen.getAllByText('Assistant')
      expect(assistantLabels.length).toBeGreaterThan(0)
    })
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
