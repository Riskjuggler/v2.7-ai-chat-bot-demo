/**
 * Mock LLM server fixture for E2E testing
 * Provides predictable responses for automated tests
 */

import { test as base } from '@playwright/test'

export interface MockLLMOptions {
  response?: string
  delay?: number
  shouldFail?: boolean
  statusCode?: number
}

/**
 * Mock LLM responses for testing
 */
export const mockLLMResponses = {
  default: 'This is a mock response from the LLM for testing purposes.',
  error: 'Error response for testing error handling.',
  timeout: 'This response should timeout.',
}

/**
 * Setup mock LLM responses using route interception
 */
export const test = base.extend<{ mockLLM: (options?: MockLLMOptions) => Promise<void> }>({
  mockLLM: async ({ page }, use) => {
    const mockLLM = async (options: MockLLMOptions = {}) => {
      const {
        response = mockLLMResponses.default,
        delay = 0,
        shouldFail = false,
        statusCode = shouldFail ? 503 : 200,
      } = options

      await page.route('**/chat', async (route) => {
        // Simulate delay if specified
        if (delay > 0) {
          await new Promise((resolve) => setTimeout(resolve, delay))
        }

        // Return error response if shouldFail is true
        if (shouldFail) {
          await route.fulfill({
            status: statusCode,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Service unavailable',
              detail: 'Mock LLM error for testing',
            }),
          })
          return
        }

        // Return successful mock response
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            response,
            model: 'mock-model',
            timestamp: new Date().toISOString(),
          }),
        })
      })
    }

    await use(mockLLM)
  },
})

export { expect } from '@playwright/test'
