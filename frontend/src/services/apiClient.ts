/**
 * API client for communicating with the FastAPI backend
 * Handles HTTP requests, error handling, and retries
 */

import { ChatRequest, ChatResponse, ErrorResponse, HealthResponse } from '../types/api'

/**
 * Custom error class for API-related errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Configuration options for the API client
 */
export interface ApiClientConfig {
  baseUrl?: string
  timeout?: number
  maxRetries?: number
  retryDelay?: number
}

/**
 * API client for backend communication
 */
export class ApiClient {
  private readonly baseUrl: string
  private readonly timeout: number
  private readonly maxRetries: number
  private readonly retryDelay: number

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = config.baseUrl || 'http://localhost:8000'
    this.timeout = config.timeout || 30000 // 30 seconds
    this.maxRetries = config.maxRetries || 2
    this.retryDelay = config.retryDelay || 1000 // 1 second
  }

  /**
   * Send a message to the LLM via the /chat endpoint
   *
   * @param request - Chat request with message
   * @returns Promise resolving to chat response
   * @throws ApiError if request fails after retries
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.fetchWithRetry<ChatResponse>('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })
  }

  /**
   * Check health of the backend API and LLM service
   *
   * @returns Promise resolving to health status
   * @throws ApiError if health check fails
   */
  async checkHealth(): Promise<HealthResponse> {
    return this.fetchWithRetry<HealthResponse>('/health', {
      method: 'GET',
    })
  }

  /**
   * Internal fetch with retry logic and timeout handling
   *
   * @param endpoint - API endpoint path
   * @param options - Fetch options
   * @returns Promise resolving to typed response
   * @throws ApiError on failure
   */
  private async fetchWithRetry<T>(
    endpoint: string,
    options: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    let lastError: Error | null = null

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        // Add timeout to fetch
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), this.timeout)

        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        // Handle HTTP error responses
        if (!response.ok) {
          const errorData: ErrorResponse = await response.json()
          throw new ApiError(
            errorData.error || 'API request failed',
            response.status,
            errorData.detail
          )
        }

        // Parse and return successful response
        const data: T = await response.json()
        return data
      } catch (error) {
        lastError = error as Error

        // Don't retry on client errors (4xx) except 408 (timeout)
        if (error instanceof ApiError && error.statusCode) {
          if (error.statusCode >= 400 && error.statusCode < 500 && error.statusCode !== 408) {
            throw error
          }
        }

        // Check if this was an abort (timeout)
        if (error instanceof Error && error.name === 'AbortError') {
          lastError = new ApiError('Request timeout', 408, `Request exceeded ${this.timeout}ms`)
        }

        // Retry if we haven't exhausted retries
        if (attempt < this.maxRetries) {
          await this.sleep(this.retryDelay)
          continue
        }

        // All retries exhausted, throw the error
        if (lastError instanceof ApiError) {
          throw lastError
        }

        // Wrap unknown errors
        throw new ApiError(
          'Network error',
          undefined,
          lastError?.message || 'Unknown error occurred'
        )
      }
    }

    // Should never reach here, but TypeScript needs it
    throw new ApiError('Request failed after retries', undefined, lastError?.message)
  }

  /**
   * Sleep utility for retry delays
   *
   * @param ms - Milliseconds to sleep
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }
}

/**
 * Default API client instance
 */
export const apiClient = new ApiClient()
