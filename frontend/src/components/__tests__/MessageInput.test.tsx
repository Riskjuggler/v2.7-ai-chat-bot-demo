import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MessageInput } from '../MessageInput'

describe('MessageInput', () => {
  it('renders textarea and send button', () => {
    const mockOnSend = vi.fn()
    render(<MessageInput onSendMessage={mockOnSend} />)

    expect(screen.getByLabelText('Message input')).toBeInTheDocument()
    expect(screen.getByLabelText('Send message')).toBeInTheDocument()
  })

  it('updates textarea value when typing', async () => {
    const mockOnSend = vi.fn()
    const user = userEvent.setup()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement
    await user.type(textarea, 'Test message')

    expect(textarea.value).toBe('Test message')
  })

  it('calls onSendMessage when send button clicked with valid input', async () => {
    const mockOnSend = vi.fn()
    const user = userEvent.setup()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    await user.type(textarea, 'Hello')
    await user.click(sendButton)

    expect(mockOnSend).toHaveBeenCalledWith('Hello')
    expect(mockOnSend).toHaveBeenCalledTimes(1)
  })

  it('clears input after sending message', async () => {
    const mockOnSend = vi.fn()
    const user = userEvent.setup()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement
    const sendButton = screen.getByLabelText('Send message')

    await user.type(textarea, 'Hello')
    await user.click(sendButton)

    expect(textarea.value).toBe('')
  })

  it('does not call onSendMessage with empty input', async () => {
    const mockOnSend = vi.fn()
    const user = userEvent.setup()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const sendButton = screen.getByLabelText('Send message')
    await user.click(sendButton)

    expect(mockOnSend).not.toHaveBeenCalled()
  })

  it('trims whitespace from message before sending', async () => {
    const mockOnSend = vi.fn()
    const user = userEvent.setup()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    await user.type(textarea, '  Hello  ')
    await user.click(sendButton)

    expect(mockOnSend).toHaveBeenCalledWith('Hello')
  })

  it('sends message when Enter key pressed', async () => {
    const mockOnSend = vi.fn()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const textarea = screen.getByLabelText('Message input')
    await userEvent.type(textarea, 'Test message')

    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    expect(mockOnSend).toHaveBeenCalledWith('Test message')
  })

  it('does not send message when Shift+Enter pressed', async () => {
    const mockOnSend = vi.fn()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const textarea = screen.getByLabelText('Message input')
    await userEvent.type(textarea, 'Test message')

    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })

    expect(mockOnSend).not.toHaveBeenCalled()
  })

  it('disables textarea when disabled prop is true', () => {
    const mockOnSend = vi.fn()
    render(<MessageInput onSendMessage={mockOnSend} disabled={true} />)

    const textarea = screen.getByLabelText('Message input')
    expect(textarea).toBeDisabled()
  })

  it('disables send button when disabled prop is true', () => {
    const mockOnSend = vi.fn()
    render(<MessageInput onSendMessage={mockOnSend} disabled={true} />)

    const sendButton = screen.getByLabelText('Send message')
    expect(sendButton).toBeDisabled()
  })

  it('disables send button when input is empty', () => {
    const mockOnSend = vi.fn()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const sendButton = screen.getByLabelText('Send message')
    expect(sendButton).toBeDisabled()
  })

  it('enables send button when input has text', async () => {
    const mockOnSend = vi.fn()
    const user = userEvent.setup()
    render(<MessageInput onSendMessage={mockOnSend} />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    expect(sendButton).toBeDisabled()

    await user.type(textarea, 'H')

    expect(sendButton).not.toBeDisabled()
  })

  it('does not send when disabled even if button clicked', async () => {
    const mockOnSend = vi.fn()
    const user = userEvent.setup()
    render(<MessageInput onSendMessage={mockOnSend} disabled={true} />)

    const textarea = screen.getByLabelText('Message input')
    const sendButton = screen.getByLabelText('Send message')

    // Manually set value (can't type when disabled)
    fireEvent.change(textarea, { target: { value: 'Test' } })
    await user.click(sendButton)

    expect(mockOnSend).not.toHaveBeenCalled()
  })
})
