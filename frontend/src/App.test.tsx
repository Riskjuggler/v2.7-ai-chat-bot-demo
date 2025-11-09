import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders the heading', () => {
    render(<App />)
    const heading = screen.getByRole('heading', { name: /AI Chat Interface/i })
    expect(heading).toBeInTheDocument()
  })

  it('renders the placeholder text', () => {
    render(<App />)
    const placeholder = screen.getByText(/Frontend scaffold ready/i)
    expect(placeholder).toBeInTheDocument()
  })

  it('mounts without errors', () => {
    const { container } = render(<App />)
    expect(container).toBeInTheDocument()
  })

  it('has correct container structure', () => {
    const { container } = render(<App />)
    const appContainer = container.querySelector('.app-container')
    expect(appContainer).toBeInTheDocument()
  })
})
