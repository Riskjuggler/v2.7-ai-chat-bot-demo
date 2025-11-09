/**
 * Unit tests for API client
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ApiClient, ApiError } from './apiClient'
import { ChatResponse, HealthResponse } from '../types/api'

describe('ApiClient', () => {
  let apiClient: ApiClient
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Create API client with short timeout for tests
    apiClient = new ApiClient({
      baseUrl: 'http://localhost:8000',
      timeout: 5000,
      maxRetries: 2,
      retryDelay: 100,
    })

    // Mock global fetch
    fetchMock = vi.fn()
    global.fetch = fetchMock
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('sendMessage', () => {
    it('should send message and return response', async () => {
      const mockResponse: ChatResponse = {
        response: 'Hello from LLM',
        model: 'gpt-3.5-turbo',
        timestamp: '2025-11-09T15:00:00',
      }

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce(mockResponse),
      } as any)

      const result = await apiClient.sendMessage({ message: 'Hello' })

      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:8000/chat',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: 'Hello' }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle API error response', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: vi.fn().mockResolvedValueOnce({
          error: 'Service unavailable',
          detail: 'LLM timeout',
        }),
      } as any)

      try {
        await apiClient.sendMessage({ message: 'Hello' })
        throw new Error('Should have thrown')
      } catch (error: any) {
        expect(error).toBeInstanceOf(ApiError)
        expect(error.message).toBe('Service unavailable')
        expect(error.statusCode).toBe(503)
        expect(error.detail).toBe('LLM timeout')
      }
    })

    it('should retry on 5xx errors', async () => {
      // First call fails with 500
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValueOnce({
          error: 'Internal server error',
        }),
      } as any)

      // Second call succeeds
      const mockResponse: ChatResponse = {
        response: 'Success after retry',
        model: 'gpt-3.5-turbo',
        timestamp: '2025-11-09T15:00:00',
      }
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce(mockResponse),
      } as any)

      const result = await apiClient.sendMessage({ message: 'Hello' })

      expect(fetchMock).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockResponse)
    })

    it('should not retry on 4xx errors (except 408)', async () => {
      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: vi.fn().mockResolvedValueOnce({
          error: 'Validation error',
          detail: 'Message too long',
        }),
      } as any)

      await expect(apiClient.sendMessage({ message: 'x'.repeat(20000) })).rejects.toThrow(
        ApiError
      )

      // Should only be called once (no retries)
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })

    it('should handle network errors with retry', async () => {
      // First two calls fail with network error
      fetchMock.mockRejectedValueOnce(new Error('Network error'))
      fetchMock.mockRejectedValueOnce(new Error('Network error'))

      // Third call succeeds
      const mockResponse: ChatResponse = {
        response: 'Success after network retry',
        model: 'gpt-3.5-turbo',
        timestamp: '2025-11-09T15:00:00',
      }
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce(mockResponse),
      } as any)

      const result = await apiClient.sendMessage({ message: 'Hello' })

      expect(fetchMock).toHaveBeenCalledTimes(3)
      expect(result).toEqual(mockResponse)
    })

    it('should throw error after max retries exhausted', async () => {
      // All calls fail
      fetchMock.mockRejectedValue(new Error('Network error'))

      await expect(apiClient.sendMessage({ message: 'Hello' })).rejects.toThrow(
        ApiError
      )

      // Should be called 3 times (1 initial + 2 retries)
      expect(fetchMock).toHaveBeenCalledTimes(3)
    })

    it('should handle timeout', async () => {
      // Create client with very short timeout
      const timeoutClient = new ApiClient({
        baseUrl: 'http://localhost:8000',
        timeout: 10, // 10ms
        maxRetries: 0,
      })

      // Mock fetch to reject with AbortError (simulating timeout)
      const abortError = new Error('The operation was aborted')
      abortError.name = 'AbortError'
      fetchMock.mockRejectedValueOnce(abortError)

      try {
        await timeoutClient.sendMessage({ message: 'Hello' })
        throw new Error('Should have thrown timeout')
      } catch (error: any) {
        expect(error).toBeInstanceOf(ApiError)
        expect(error.message).toBe('Request timeout')
        expect(error.statusCode).toBe(408)
      }
    })
  })

  describe('checkHealth', () => {
    it('should check health and return status', async () => {
      const mockResponse: HealthResponse = {
        status: 'healthy',
        llm_available: true,
      }

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce(mockResponse),
      } as any)

      const result = await apiClient.checkHealth()

      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({
          method: 'GET',
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle unhealthy status', async () => {
      const mockResponse: HealthResponse = {
        status: 'healthy',
        llm_available: false,
      }

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce(mockResponse),
      } as any)

      const result = await apiClient.checkHealth()

      expect(result.llm_available).toBe(false)
    })
  })

  describe('ApiError', () => {
    it('should create error with message only', () => {
      const error = new ApiError('Test error')
      expect(error.message).toBe('Test error')
      expect(error.name).toBe('ApiError')
      expect(error.statusCode).toBeUndefined()
      expect(error.detail).toBeUndefined()
    })

    it('should create error with status code and detail', () => {
      const error = new ApiError('API failed', 500, 'Internal error')
      expect(error.message).toBe('API failed')
      expect(error.statusCode).toBe(500)
      expect(error.detail).toBe('Internal error')
    })
  })
})
