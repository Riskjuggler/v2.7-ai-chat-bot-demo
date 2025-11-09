# Architecture Documentation

This document describes the design decisions, technical stack, and architectural patterns used in the AI Chat Web Interface.

## Table of Contents

- [System Overview](#system-overview)
- [Technology Stack](#technology-stack)
- [Component Architecture](#component-architecture)
- [API Design](#api-design)
- [Integration Patterns](#integration-patterns)
- [Security Architecture](#security-architecture)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)

## System Overview

The AI Chat Web Interface is a client-server application that provides a web-based chat interface for interacting with multiple LLM providers.

### High-Level Architecture

```
┌─────────────────┐       HTTP/REST      ┌──────────────────┐
│                 │ ───────────────────> │                  │
│  React Frontend │                      │  FastAPI Backend │
│  (Port 3000)    │ <─────────────────── │  (Port 8000)     │
│                 │      JSON Response    │                  │
└─────────────────┘                      └──────────────────┘
                                                  │
                                                  │ Unified Interface
                                                  ▼
                               ┌──────────────────────────────────┐
                               │   LLM Caller CLI Module          │
                               │  (llm_caller_cli)                │
                               └──────────────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
              ┌──────────┐          ┌──────────┐         ┌──────────┐
              │ OpenAI   │          │Anthropic │         │LM Studio │
              │ Provider │          │ Provider │         │ (Local)  │
              └──────────┘          └──────────┘         └──────────┘
```

### Key Principles

1. **Separation of Concerns**: Clear boundaries between frontend, backend, and LLM integration
2. **Provider Abstraction**: Unified interface for multiple LLM providers
3. **Security First**: Localhost-only by default, no credentials in code
4. **Testability**: High test coverage with unit, integration, and E2E tests
5. **Simplicity**: Straightforward architecture without over-engineering

## Technology Stack

### Frontend

- **React 18**: UI framework with modern concurrent rendering
- **TypeScript**: Type safety and better developer experience
- **Vite**: Fast build tool and dev server
- **Vitest**: Testing framework for React components
- **CSS Modules**: Component-scoped styling

**Why React?**
- Mature ecosystem with excellent tooling
- Component-based architecture matches our UI needs
- Strong TypeScript support
- Fast development with hot module replacement

**Why TypeScript?**
- Catch errors at compile time vs runtime
- Better IDE support with autocomplete
- Self-documenting code with type definitions
- Easier refactoring and maintenance

### Backend

- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server for async request handling
- **Pydantic**: Data validation and settings management
- **Python 3.9+**: Modern Python with type hints
- **Pytest**: Testing framework with async support

**Why FastAPI?**
- Automatic API documentation (OpenAPI/Swagger)
- Built-in validation with Pydantic
- Native async/await support for concurrent requests
- Type hints for better code quality
- Fast performance (comparable to Node.js/Go)

**Why Async?**
- LLM API calls can take seconds (streaming responses)
- Async allows handling multiple concurrent chat sessions
- Non-blocking I/O for better resource utilization

### LLM Integration

- **llm_caller_cli**: Custom module for unified LLM access
- **OpenAI SDK**: Official OpenAI Python client
- **Anthropic SDK**: Official Anthropic Python client
- **OpenAI-compatible API**: For LM Studio (local models)

**Why Custom Module?**
- Abstracts provider-specific details
- Enables intelligent model routing
- Provides fallback and retry logic
- Centralizes configuration management
- Reusable across projects

## Component Architecture

### Frontend Components

```
src/
├── App.tsx                    # Main app container
├── components/
│   ├── ChatInterface.tsx      # Main chat UI
│   ├── MessageList.tsx        # Message history display
│   ├── MessageInput.tsx       # User input form
│   ├── Message.tsx            # Individual message component
│   └── ModelSelector.tsx      # LLM model picker
├── services/
│   └── api.ts                 # API client (fetch wrapper)
├── types/
│   └── chat.ts                # TypeScript type definitions
└── utils/
    └── formatters.ts          # Utility functions
```

**Component Responsibilities**:

- **App.tsx**: Application root, global state, routing (if added later)
- **ChatInterface**: Manages chat session state, coordinates child components
- **MessageList**: Renders message history with auto-scroll
- **MessageInput**: Handles user input, validation, submission
- **Message**: Displays a single message with role (user/assistant)
- **ModelSelector**: Allows switching between available models

**State Management**:
- Local component state with `useState`
- Props for parent-child communication
- No global state library (not needed for simple chat)

### Backend Components

```
src/api/
├── main.py                    # FastAPI app setup
├── routes.py                  # API endpoints
├── models.py                  # Pydantic models
├── llm_service.py             # LLM integration service
├── middleware.py              # Security middleware
└── config.py                  # Configuration
```

**Component Responsibilities**:

- **main.py**: App initialization, CORS, middleware setup
- **routes.py**: API endpoint definitions (chat, models, health)
- **models.py**: Request/response schemas with validation
- **llm_service.py**: Abstraction layer for LLM calls
- **middleware.py**: Localhost-only security enforcement
- **config.py**: Environment variable management

**Layered Architecture**:
```
Routes (HTTP) → Service Layer → LLM Caller Module → Provider APIs
```

### LLM Caller Module

```
llm_caller_cli/
├── src/
│   ├── core/
│   │   ├── llm_caller.py      # Main caller interface
│   │   └── router.py          # Intelligent routing
│   ├── providers/
│   │   ├── openai.py          # OpenAI implementation
│   │   ├── anthropic.py       # Anthropic implementation
│   │   └── lmstudio.py        # LM Studio implementation
│   ├── config/
│   │   └── settings.py        # Configuration management
│   └── models/
│       └── schemas.py         # Data models
└── tests/                     # 241 tests
```

**Design Pattern**: Strategy pattern for provider implementations

## API Design

### REST Endpoints

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/health` | GET | Health check | None | `{"status": "healthy"}` |
| `/models` | GET | List available models | None | `{"models": [{"id": "gpt-4", ...}]}` |
| `/chat` | POST | Send chat message | `ChatRequest` | `ChatResponse` |

### Request/Response Models

**ChatRequest**:
```json
{
  "message": "Hello, how are you?",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**ChatResponse**:
```json
{
  "response": "I'm doing well, thank you!",
  "model": "gpt-4",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 20,
    "total_tokens": 35
  }
}
```

### Error Handling

**Standard Error Response**:
```json
{
  "detail": "Error message here",
  "code": "ERROR_CODE"
}
```

**HTTP Status Codes**:
- `200 OK`: Successful request
- `400 Bad Request`: Invalid input (validation error)
- `401 Unauthorized`: Invalid API key
- `403 Forbidden`: Not localhost (security middleware)
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: LLM provider unavailable

## Integration Patterns

### Provider Abstraction

**Interface**:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[dict], **kwargs) -> str:
        """Send chat request and return response."""
        pass

    @abstractmethod
    async def list_models(self) -> List[Model]:
        """List available models."""
        pass
```

**Benefits**:
- Swap providers without changing application code
- Easy to add new providers
- Consistent error handling across providers
- Testable with mock providers

### Configuration Management

**Hierarchy**:
1. Environment variables (`.env` file)
2. Default values (in code)
3. Runtime overrides (API parameters)

**Pattern**: Settings object (Pydantic BaseSettings)

```python
class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    lmstudio_base_url: str = "http://localhost:1234/v1"

    class Config:
        env_file = ".env"
```

### Error Handling Strategy

**Layers**:
1. **Provider Layer**: Retry logic, fallback to alternative models
2. **Service Layer**: Map provider errors to application errors
3. **API Layer**: Return appropriate HTTP status codes
4. **Frontend**: Display user-friendly error messages

**Example Flow**:
```
OpenAI timeout → Service retries → Falls back to GPT-3.5 → Returns response
OR
All providers fail → Service raises error → API returns 503 → UI shows "Service unavailable"
```

## Security Architecture

### Threat Model

**Protected Against**:
- Remote access (localhost-only middleware)
- API key exposure (`.env` file, gitignored)
- CORS attacks (strict origin validation)
- Injection attacks (Pydantic validation)

**Not Protected Against** (by design, local dev tool):
- Local privilege escalation
- Physical access attacks
- Network sniffing (no HTTPS in dev)

### Security Layers

1. **Localhost-Only Middleware**: Rejects non-localhost requests
2. **CORS**: Only allows specific origins (ports 3000, 5173)
3. **Input Validation**: Pydantic models validate all inputs
4. **Credential Management**: API keys in environment variables only
5. **Dependencies**: Regular security scanning with `pip-audit`

### Configuration Security

```python
# middleware.py
class LocalhostOnlyMiddleware:
    async def __call__(self, request: Request, call_next):
        host = request.client.host
        if host not in ["127.0.0.1", "localhost", "::1"]:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access forbidden: not localhost"}
            )
        return await call_next(request)
```

## Data Flow

### Chat Message Flow

```
1. User types message in frontend
   └─> MessageInput.tsx validates input
       └─> ChatInterface.tsx updates local state
           └─> api.ts sends POST /chat request
               └─> routes.py receives request
                   └─> llm_service.py processes
                       └─> llm_caller selects provider
                           └─> Provider API call
                               └─> Response flows back up
                                   └─> Frontend updates UI
```

### Model Selection Flow

```
1. Frontend requests available models (GET /models)
   └─> Backend queries llm_caller.list_models()
       └─> Each provider lists its models
           └─> Router ranks by capability
               └─> Returns ranked list
                   └─> Frontend displays in dropdown
                       └─> User selects model
                           └─> Subsequent chats use selected model
```

## Design Decisions

### Why FastAPI over Flask/Django?

**Considered**:
- Flask: Simpler but lacks async, no automatic API docs
- Django: Too heavy for a simple chat API
- FastAPI: Modern, async, auto docs, validation

**Decision**: FastAPI for async support and automatic documentation.

### Why No Database?

**Current**: Stateless API, messages not persisted

**Rationale**:
- Chat sessions are temporary (single-page app)
- No user accounts (localhost only)
- Simplicity over features

**Future**: Could add SQLite or PostgreSQL for chat history if needed.

### Why No WebSocket Streaming?

**Current**: REST API with synchronous responses

**Rationale**:
- Simpler to implement and test
- HTTP/2 server-sent events possible later
- Adequate for typical chat latency (2-5 seconds)

**Future**: Could add WebSocket for real-time streaming if needed.

### Why Separate llm_caller_cli Module?

**Rationale**:
- Reusable across projects (standalone module)
- Clear separation of concerns
- Independently testable (241 tests)
- Potential for CLI tool or library

**Trade-off**: Extra abstraction layer, but worth it for maintainability.

### Why Vite over Create React App?

**Considered**:
- Create React App: More common but slower
- Vite: Faster dev server, better DX

**Decision**: Vite for speed and modern tooling.

### Why No State Management Library?

**Current**: Local component state with `useState`

**Rationale**:
- Simple application with limited state
- Props drilling not a problem yet
- Avoids Redux/MobX complexity

**Future**: If app grows to multiple pages or complex state, consider Zustand or Jotai.

## Performance Considerations

### Backend

- **Async I/O**: Non-blocking LLM API calls
- **Connection Pooling**: Reuse HTTP connections to providers
- **Caching**: Model metadata cached to reduce API calls

### Frontend

- **Code Splitting**: Vite automatically splits chunks
- **Lazy Loading**: Components loaded on demand
- **Memoization**: React.memo for expensive renders

### LLM Calls

- **Streaming**: Future enhancement for real-time responses
- **Timeout**: 30-second timeout prevents hanging requests
- **Retry Logic**: Automatic retry with exponential backoff

## Testing Architecture

### Test Pyramid

```
        E2E Tests (few)
       /              \
    Integration Tests
   /                    \
Unit Tests (many)
```

**Distribution**:
- Unit tests: ~80% (fast, isolated)
- Integration tests: ~15% (API + service)
- E2E tests: ~5% (full flow)

### Test Strategy

- **Backend**: Pytest with async support, mocks for LLM providers
- **Frontend**: Vitest with React Testing Library
- **E2E**: Pytest with HTTP client, tests full API flow
- **Coverage**: >90% backend, >80% frontend

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Future Enhancements

### Potential Improvements

1. **WebSocket Streaming**: Real-time response streaming
2. **Chat History**: Persist conversations in database
3. **User Authentication**: Support multiple users
4. **Model Comparison**: Side-by-side comparison of different models
5. **Advanced Routing**: Cost-based or latency-based model selection
6. **Response Caching**: Cache common queries
7. **Rate Limiting**: Prevent API abuse
8. **Docker Deployment**: Containerized deployment
9. **System Prompts**: Customizable system prompts
10. **File Uploads**: Support for document/image uploads

### Scalability Considerations

**Current**: Single-server, localhost-only

**If Scaling Needed**:
- Add load balancer for multiple backend instances
- Use Redis for shared session state
- Implement rate limiting per user/IP
- Add monitoring and logging (Prometheus, Grafana)
- Deploy to cloud (AWS, GCP, Azure)

## Conclusion

The architecture prioritizes simplicity, security, and testability for a localhost development tool. The modular design allows easy extension (new providers, features) while maintaining clear separation of concerns.

For questions or suggestions, see the main [README.md](../README.md) or open an issue.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
