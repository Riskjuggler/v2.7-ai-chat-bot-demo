/**
 * TypeScript type definitions for API communication
 * Matches backend FastAPI schemas in src/api/schemas.py
 */

/**
 * Request payload for the /chat endpoint
 */
export interface ChatRequest {
  message: string
}

/**
 * Response from the /chat endpoint
 */
export interface ChatResponse {
  response: string
  model: string
  timestamp: string
}

/**
 * Error response from the API
 */
export interface ErrorResponse {
  error: string
  detail?: string
}

/**
 * Health check response from /health endpoint
 */
export interface HealthResponse {
  status: string
  llm_available: boolean
}
