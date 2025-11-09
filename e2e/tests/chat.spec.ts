/**
 * End-to-end tests for chat functionality
 * Tests the complete user flow from frontend to backend
 */

import { test, expect } from '../fixtures/mockLLM'

test.describe('Chat Interface E2E Tests', () => {
  test.describe('Happy Path', () => {
    test('user can send message and receive response', async ({ page, mockLLM }) => {
      // Setup mock LLM response
      await mockLLM({
        response: 'Hello! This is a test response from the mock LLM.',
      })

      // Navigate to chat page
      await page.goto('/')

      // Verify initial empty state
      await expect(page.getByText('No messages yet')).toBeVisible()

      // Type a message
      const input = page.getByRole('textbox', { name: /type your message/i })
      await input.fill('Hello, can you help me?')

      // Send message
      const sendButton = page.getByRole('button', { name: /send/i })
      await sendButton.click()

      // Verify user message appears
      await expect(page.getByText('Hello, can you help me?')).toBeVisible()

      // Verify loading indicator appears
      await expect(page.locator('.loading-indicator')).toBeVisible()

      // Verify assistant response appears
      await expect(
        page.getByText('Hello! This is a test response from the mock LLM.')
      ).toBeVisible()

      // Verify loading indicator disappears
      await expect(page.locator('.loading-indicator')).not.toBeVisible()

      // Verify input is cleared and ready for next message
      await expect(input).toHaveValue('')
      await expect(sendButton).not.toBeDisabled()
    })

    test('user can send multiple messages in sequence', async ({ page, mockLLM }) => {
      await mockLLM({
        response: 'Response to message',
      })

      await page.goto('/')

      // Send first message
      const input = page.getByRole('textbox')
      await input.fill('First message')
      await page.getByRole('button', { name: /send/i }).click()
      await expect(page.getByText('First message')).toBeVisible()
      await expect(page.getByText('Response to message')).toBeVisible()

      // Send second message
      await input.fill('Second message')
      await page.getByRole('button', { name: /send/i }).click()
      await expect(page.getByText('Second message')).toBeVisible()

      // Verify both messages and responses are visible
      const messages = page.locator('[role="log"] > *')
      await expect(messages).toHaveCount(4) // 2 user + 2 assistant
    })

    test('messages scroll to bottom automatically', async ({ page, mockLLM }) => {
      await mockLLM({
        response: 'Short response',
      })

      await page.goto('/')

      // Send multiple messages to create scroll
      const input = page.getByRole('textbox')
      for (let i = 1; i <= 10; i++) {
        await input.fill(`Message ${i}`)
        await page.getByRole('button', { name: /send/i }).click()
        await page.waitForTimeout(200) // Wait for response
      }

      // Verify last message is visible (scrolled to bottom)
      await expect(page.getByText('Message 10')).toBeVisible()
    })
  })

  test.describe('Error Scenarios', () => {
    test('displays error when backend returns 503', async ({ page, mockLLM }) => {
      // Setup mock to return error
      await mockLLM({
        shouldFail: true,
        statusCode: 503,
      })

      await page.goto('/')

      // Send message
      const input = page.getByRole('textbox')
      await input.fill('This should fail')
      await page.getByRole('button', { name: /send/i }).click()

      // Verify user message appears
      await expect(page.getByText('This should fail')).toBeVisible()

      // Verify error message appears
      await expect(
        page.getByText(/LLM service is currently unavailable/i)
      ).toBeVisible()

      // Verify error has proper ARIA role
      const errorAlert = page.getByRole('alert')
      await expect(errorAlert).toBeVisible()
    })

    test('displays error on network failure', async ({ page }) => {
      // Abort all requests to /chat to simulate network failure
      await page.route('**/chat', (route) => route.abort('failed'))

      await page.goto('/')

      // Send message
      const input = page.getByRole('textbox')
      await input.fill('This will fail')
      await page.getByRole('button', { name: /send/i }).click()

      // Verify error message appears
      await expect(page.getByRole('alert')).toBeVisible()
    })

    test('displays error on timeout', async ({ page, mockLLM }) => {
      // Setup mock with long delay to trigger timeout
      await mockLLM({
        delay: 35000, // Longer than API client timeout (30s)
      })

      await page.goto('/')

      // Send message
      const input = page.getByRole('textbox')
      await input.fill('This will timeout')
      await page.getByRole('button', { name: /send/i }).click()

      // Verify timeout error appears (with reasonable timeout for test)
      await expect(page.getByText(/timeout/i)).toBeVisible({ timeout: 40000 })
    })

    test('prevents sending empty messages', async ({ page }) => {
      await page.goto('/')

      // Try to send empty message
      const sendButton = page.getByRole('button', { name: /send/i })
      await expect(sendButton).toBeDisabled()

      // Verify button enables when text is entered
      const input = page.getByRole('textbox')
      await input.fill('Some text')
      await expect(sendButton).not.toBeDisabled()

      // Verify button disables again when text is cleared
      await input.clear()
      await expect(sendButton).toBeDisabled()
    })

    test('clears previous errors when sending new message', async ({ page, mockLLM }) => {
      // First request fails
      await mockLLM({
        shouldFail: true,
        statusCode: 503,
      })

      await page.goto('/')

      const input = page.getByRole('textbox')

      // Send message that will fail
      await input.fill('Fail message')
      await page.getByRole('button', { name: /send/i }).click()
      await expect(page.getByRole('alert')).toBeVisible()

      // Setup mock for success
      await mockLLM({
        response: 'Success response',
      })

      // Send new message
      await input.fill('Success message')
      await page.getByRole('button', { name: /send/i }).click()

      // Verify previous error is cleared
      await expect(page.getByRole('alert')).not.toBeVisible()
      await expect(page.getByText('Success response')).toBeVisible()
    })
  })

  test.describe('Loading States', () => {
    test('disables input during API call', async ({ page, mockLLM }) => {
      await mockLLM({
        delay: 1000,
        response: 'Delayed response',
      })

      await page.goto('/')

      const input = page.getByRole('textbox')
      const sendButton = page.getByRole('button', { name: /send/i })

      // Send message
      await input.fill('Test message')
      await sendButton.click()

      // Verify input and button are disabled during loading
      await expect(sendButton).toBeDisabled()

      // Wait for response
      await expect(page.getByText('Delayed response')).toBeVisible()

      // Verify input and button are re-enabled
      await expect(sendButton).not.toBeDisabled()
    })

    test('shows loading indicator during API call', async ({ page, mockLLM }) => {
      await mockLLM({
        delay: 1000,
        response: 'Response after loading',
      })

      await page.goto('/')

      // Send message
      const input = page.getByRole('textbox')
      await input.fill('Test')
      await page.getByRole('button', { name: /send/i }).click()

      // Verify loading indicator appears
      await expect(page.locator('.loading-indicator')).toBeVisible()

      // Wait for response
      await expect(page.getByText('Response after loading')).toBeVisible()

      // Verify loading indicator disappears
      await expect(page.locator('.loading-indicator')).not.toBeVisible()
    })
  })

  test.describe('Accessibility', () => {
    test('has proper ARIA labels', async ({ page }) => {
      await page.goto('/')

      // Verify chat messages area has role and label
      await expect(page.getByRole('log')).toHaveAttribute('aria-label', 'Chat messages')

      // Verify textbox is labeled
      await expect(page.getByRole('textbox')).toBeVisible()

      // Verify send button is labeled
      await expect(page.getByRole('button', { name: /send/i })).toBeVisible()
    })

    test('error messages have alert role and aria-live', async ({ page, mockLLM }) => {
      await mockLLM({
        shouldFail: true,
        statusCode: 503,
      })

      await page.goto('/')

      // Send message to trigger error
      await page.getByRole('textbox').fill('Error test')
      await page.getByRole('button', { name: /send/i }).click()

      // Verify error has proper accessibility attributes
      const alert = page.getByRole('alert')
      await expect(alert).toBeVisible()
      await expect(alert).toHaveAttribute('aria-live', 'assertive')
    })
  })
})
