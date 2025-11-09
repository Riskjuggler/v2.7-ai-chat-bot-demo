# Integration Guide

This document explains how the frontend and backend are integrated in the AI Chat Web Interface.

## Architecture Overview

The system follows a clean separation between frontend and backend:

```
┌─────────────────────────────────────────────┐
│           Frontend (React + Vite)           │
│                                             │
│  ┌──────────────┐      ┌────────────────┐  │
│  │   UI Layer   │      │  Service Layer │  │
│  │              │──────│                │  │
│  │ ChatContainer│      │   apiClient    │  │
│  │ ChatMessage  │      │                │  │
│  │ MessageInput │      │                │  │
│  └──────────────┘      └────────┬───────┘  │
│                                 │          │
└─────────────────────────────────┼──────────┘
                                  │
                              HTTP/JSON
                                  │
┌─────────────────────────────────┼──────────┐
│           Backend (FastAPI)     │          │
│                                 │          │
│  ┌──────────────┐      ┌────────▼───────┐  │
│  │   Routes     │      │    Service     │  │
│  │              │──────│                │  │
│  │ POST /chat   │      │  LLMService    │  │
│  │ GET /health  │      │                │  │
│  └──────────────┘      └────────┬───────┘  │
│                                 │          │
└─────────────────────────────────┼──────────┘
                                  │
                           LLM Caller CLI
                                  │
                    ┌─────────────┼──────────────┐
                    │             │              │
                    ▼             ▼              ▼
                LM Studio     OpenAI        Anthropic
```

## API Client

The API client (`frontend/src/services/apiClient.ts`) handles all communication with the backend.

### Features

- **Type-safe requests/responses** using TypeScript interfaces
- **Automatic retries** for transient failures
- **Timeout handling** with configurable limits
- **Error handling** with custom error types
- **Singleton pattern** for global use

### Basic Usage

```typescript
import { apiClient } from '../services/apiClient'

// Send a message to the LLM
const response = await apiClient.sendMessage({
  message: 'Hello, world!',
})

console.log(response.response)  // LLM's reply
console.log(response.model)     // Model used
console.log(response.timestamp) // Response timestamp
```

### Custom Configuration

```typescript
import { ApiClient } from '../services/apiClient'

// Create custom client with different settings
const customClient = new ApiClient({
  baseUrl: 'http://localhost:8000',
  timeout: 60000,      // 60 seconds
  maxRetries: 3,       // Retry up to 3 times
  retryDelay: 2000,    // Wait 2s between retries
})

const response = await customClient.sendMessage({
  message: 'Custom request',
})
```

## Type Definitions

TypeScript interfaces ensure type safety between frontend and backend.

### Request Schema

```typescript
// frontend/src/types/api.ts
export interface ChatRequest {
  message: string  // User's message (1-10000 chars)
}
```

Matches backend:
```python
# src/api/schemas.py
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
```

### Response Schema

```typescript
// frontend/src/types/api.ts
export interface ChatResponse {
  response: string    // LLM's reply
  model: string      // Model that generated response
  timestamp: string  // ISO 8601 timestamp
}
```

Matches backend:
```python
# src/api/schemas.py
class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: datetime
```

### Error Schema

```typescript
// frontend/src/types/api.ts
export interface ErrorResponse {
  error: string     // Error message
  detail?: string   // Optional error details
}
```

Matches backend:
```python
# src/api/schemas.py
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
```

## Error Handling

The API client provides comprehensive error handling.

### Error Types

```typescript
import { ApiError } from '../services/apiClient'

try {
  const response = await apiClient.sendMessage({ message: 'Test' })
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.message)
    console.error('Status Code:', error.statusCode)
    console.error('Details:', error.detail)
  }
}
```

### HTTP Status Codes

| Status | Meaning | Retry? | User Message |
|--------|---------|--------|--------------|
| 200 | Success | - | Display response |
| 408 | Request Timeout | Yes (2x) | "Request timed out. Please try again." |
| 422 | Validation Error | No | "Invalid message. Please check your input." |
| 500 | Internal Server Error | Yes (2x) | "Server error. Please try again." |
| 503 | Service Unavailable | Yes (2x) | "LLM service is currently unavailable." |

### Retry Logic

The API client automatically retries failed requests:

1. **Retry on 5xx errors** (server errors)
2. **Retry on network failures** (connection refused, timeout)
3. **No retry on 4xx errors** (except 408 timeout)
4. **Exponential backoff** with configurable delay

```typescript
// Default retry configuration
{
  maxRetries: 2,        // Retry up to 2 times
  retryDelay: 1000,     // Wait 1 second between retries
}

// Total attempts: 1 initial + 2 retries = 3 attempts
```

## Component Integration

### ChatContainer Component

The `ChatContainer` component orchestrates the chat interface.

#### State Management

```typescript
const [messages, setMessages] = useState<Message[]>([])
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState<string | null>(null)
```

#### Message Flow

1. **User types message** → `MessageInput` component
2. **Click send** → Calls `handleSendMessage(content)`
3. **Add user message** → Updates `messages` state
4. **Set loading** → `setIsLoading(true)`
5. **Call API** → `apiClient.sendMessage()`
6. **Handle response** → Add assistant message to `messages`
7. **Clear loading** → `setIsLoading(false)`
8. **Handle errors** → Set `error` state, display to user

#### Code Example

```typescript
const handleSendMessage = async (content: string) => {
  setError(null)

  // Add user message
  const userMessage: Message = {
    id: `user-${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date(),
  }
  setMessages((prev) => [...prev, userMessage])

  // Call API
  setIsLoading(true)
  try {
    const response = await apiClient.sendMessage({ message: content })

    // Add assistant response
    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.response,
      timestamp: new Date(response.timestamp),
    }
    setMessages((prev) => [...prev, assistantMessage])
  } catch (err) {
    // Handle errors
    setError(getErrorMessage(err))
  } finally {
    setIsLoading(false)
  }
}
```

## Backend API

### Endpoints

#### POST /chat

Send a message to the LLM and receive a response.

**Request:**
```json
{
  "message": "What is the capital of France?"
}
```

**Response (200 OK):**
```json
{
  "response": "The capital of France is Paris.",
  "model": "gpt-3.5-turbo",
  "timestamp": "2025-11-09T15:00:00"
}
```

**Error (503 Service Unavailable):**
```json
{
  "error": "LLM service unavailable",
  "detail": "Connection timeout after 30s"
}
```

#### GET /health

Check API and LLM service health.

**Response:**
```json
{
  "status": "healthy",
  "llm_available": true
}
```

### CORS Configuration

The backend allows requests only from localhost origins:

```python
# src/api/middleware.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Allowed Origins:**
- `http://localhost:3000` (Create React App default)
- `http://localhost:5173` (Vite default)

## Configuration

### Environment Variables

Both frontend and backend can be configured via environment variables.

#### Frontend Configuration

Create `frontend/.env.local`:

```bash
# API base URL (default: http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000

# Request timeout in milliseconds (default: 30000)
VITE_API_TIMEOUT=30000

# Max retries (default: 2)
VITE_API_MAX_RETRIES=2
```

Use in code:
```typescript
const apiClient = new ApiClient({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  maxRetries: Number(import.meta.env.VITE_API_MAX_RETRIES) || 2,
})
```

#### Backend Configuration

See `.env.example` for complete backend configuration (LLM providers, model settings).

## Testing Integration

### Unit Tests

Mock the API client in component tests:

```typescript
import { vi } from 'vitest'
import { apiClient } from '../services/apiClient'

vi.mock('../services/apiClient', () => ({
  apiClient: {
    sendMessage: vi.fn(),
  },
}))

test('sends message', async () => {
  apiClient.sendMessage.mockResolvedValue({
    response: 'Mock response',
    model: 'mock-model',
    timestamp: new Date().toISOString(),
  })

  // Test component...
})
```

### E2E Tests

Use Playwright route interception:

```typescript
await page.route('**/chat', async (route) => {
  await route.fulfill({
    status: 200,
    body: JSON.stringify({
      response: 'E2E test response',
      model: 'test-model',
      timestamp: new Date().toISOString(),
    }),
  })
})
```

## Troubleshooting

### Common Issues

#### "Connection refused" Error

**Cause:** Backend is not running

**Solution:**
```bash
cd src/api
python -m uvicorn main:app --reload
```

#### CORS Error in Browser

**Cause:** Frontend origin not allowed

**Solution:** Check `src/api/middleware.py` includes your frontend URL in `allow_origins`.

#### "Request timeout" Error

**Cause:** LLM taking too long to respond

**Solutions:**
1. Increase timeout: `new ApiClient({ timeout: 60000 })`
2. Check LM Studio server is responding
3. Try a faster model

#### Type Errors

**Cause:** Frontend/backend schemas out of sync

**Solution:**
1. Compare `frontend/src/types/api.ts` with `src/api/schemas.py`
2. Regenerate types if needed
3. Ensure both use same field names and types

## Best Practices

### 1. Always Handle Errors

```typescript
try {
  const response = await apiClient.sendMessage({ message })
  // Handle success
} catch (error) {
  // Always handle errors - network can fail!
  setError(getErrorMessage(error))
}
```

### 2. Use Loading States

```typescript
setIsLoading(true)
try {
  const response = await apiClient.sendMessage({ message })
  // Process response
} finally {
  setIsLoading(false)  // Always clear loading state
}
```

### 3. Clear Previous Errors

```typescript
const handleSendMessage = async (content: string) => {
  setError(null)  // Clear previous errors before new request
  // ... rest of handler
}
```

### 4. Validate Input

```typescript
if (!message.trim()) {
  return  // Don't send empty messages
}
```

### 5. Use TypeScript

```typescript
// Type-safe API calls
const response: ChatResponse = await apiClient.sendMessage(request)

// Autocomplete and type checking
response.response  // ✓ OK
response.invalid   // ✗ TypeScript error
```

## References

- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
