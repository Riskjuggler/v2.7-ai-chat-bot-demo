# AI Chat API Documentation

**Version**: 0.1.0
**Base URL**: `http://localhost:8000`

REST API for the AI Chat Web Interface, providing endpoints to communicate with LLM via the llm_caller_cli module.

---

## Quick Start

### Starting the Server

```bash
# From project root
python -m src.api.main
```

Server will start on `http://localhost:8000` (localhost only).

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Security

**Localhost-Only Access**: API only accepts requests from localhost (`127.0.0.1`, `localhost`, `::1`). External requests receive `403 Forbidden`.

**CORS**: Configured for localhost origins on ports 3000 and 5173 (Vite default).

---

## Endpoints

### POST /chat

Send a message to the LLM and receive a response.

**Request Body** (JSON):
```json
{
  "message": "string (1-10000 characters, required)"
}
```

**Success Response** (200):
```json
{
  "response": "The capital of France is Paris.",
  "model": "gpt-3.5-turbo",
  "timestamp": "2025-11-09T15:00:00"
}
```

**Error Responses**:

- **422 Validation Error**: Invalid request body
  ```json
  {
    "detail": [
      {
        "loc": ["body", "message"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
  ```

- **500 Internal Server Error**: LLM error or connection failure
  ```json
  {
    "detail": "Cannot connect to LLM service: Connection refused"
  }
  ```

- **503 Service Unavailable**: LLM timeout
  ```json
  {
    "detail": "LLM request timeout: Request timeout"
  }
  ```

**Example Request** (curl):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?"}'
```

**Example Request** (Python):
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "What is the capital of France?"}
)

data = response.json()
print(f"LLM: {data['response']}")
```

**Example Request** (JavaScript):
```javascript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'What is the capital of France?'})
});

const data = await response.json();
console.log(`LLM: ${data.response}`);
```

---

### GET /health

Check API and LLM service health.

**Success Response** (200):
```json
{
  "status": "healthy",
  "llm_available": true
}
```

**Response Fields**:
- `status`: Always "healthy" if API is running
- `llm_available`: `true` if LLM service (LM Studio) is reachable, `false` otherwise

**Example Request** (curl):
```bash
curl http://localhost:8000/health
```

**Example Request** (Python):
```python
import requests

response = requests.get("http://localhost:8000/health")
data = response.json()

if data["llm_available"]:
    print("LLM service is available")
else:
    print("LLM service is unavailable")
```

---

## Schema Reference

### ChatRequest

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `message` | string | Yes | 1-10000 chars | User message to send to LLM |

### ChatResponse

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | LLM's response text |
| `model` | string | Model name used (e.g., "gpt-3.5-turbo") |
| `timestamp` | datetime | ISO 8601 timestamp of response |

### HealthResponse

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | API status (always "healthy") |
| `llm_available` | boolean | Whether LLM service is reachable |

---

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **403 Forbidden**: Request from non-localhost IP
- **422 Unprocessable Entity**: Request validation failed
- **500 Internal Server Error**: LLM error or server error
- **503 Service Unavailable**: LLM timeout or unavailable

### Error Response Format

All errors return JSON with `detail` field:
```json
{
  "detail": "Error description"
}
```

For validation errors (422), FastAPI returns detailed field-level errors.

---

## Configuration

### LLM Settings

API uses these default settings for LM Studio:

- **Provider**: lmstudio
- **Base URL**: http://localhost:1234/v1
- **Model**: local-model
- **Timeout**: 30 seconds

To modify settings, edit `src/api/service.py` (`LLMService.__init__`).

### Server Settings

- **Host**: 127.0.0.1 (localhost only)
- **Port**: 8000
- **CORS Origins**: localhost:3000, localhost:5173

To modify, edit `src/api/main.py`.

---

## Testing

### Running Tests

```bash
# All API tests
pytest tests/api/ -v

# With coverage
pytest tests/api/ --cov=src/api --cov-report=term-missing

# Specific test file
pytest tests/api/test_routes.py -v
```

### Manual Testing with LM Studio

1. **Start LM Studio** on localhost:1234
2. **Load a model** in LM Studio
3. **Start the API**: `python -m src.api.main`
4. **Send test request**:
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Say hello"}'
   ```

---

## Deployment Notes

### Development

```bash
# Run with auto-reload
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Production (Localhost Only)

```bash
# Run with uvicorn
uvicorn src.api.main:app --host 127.0.0.1 --port 8000

# Or use the built-in runner
python -m src.api.main
```

**Note**: This API is designed for single-user desktop use only. Do NOT expose to the internet or local network.

---

## Troubleshooting

### "Cannot connect to LLM service"

- Verify LM Studio is running on localhost:1234
- Check LM Studio has a model loaded
- Check LM Studio local server is enabled

### "Forbidden" (403 Error)

- Ensure you're making requests from localhost
- Check client is using `127.0.0.1` or `localhost`, not machine IP

### "Service Unavailable" (503 Error)

- LLM request timed out (30s timeout)
- Check LM Studio performance and model size
- Consider increasing timeout in `src/api/service.py`

### Validation Errors (422)

- Check message field is present in request body
- Verify message length is 1-10000 characters
- Ensure Content-Type header is `application/json`

---

## Development

### Project Structure

```
src/api/
├── __init__.py         # Package init
├── main.py             # FastAPI app setup
├── routes.py           # Endpoint definitions
├── schemas.py          # Pydantic models
├── service.py          # LLM service layer
└── middleware.py       # Security middleware

tests/api/
├── test_routes.py      # Endpoint tests
├── test_service.py     # Service layer tests
├── test_middleware.py  # Security tests
├── test_schemas.py     # Schema validation tests
└── test_integration.py # Integration tests
```

### Adding New Endpoints

1. Define Pydantic schemas in `schemas.py`
2. Add route handler in `routes.py`
3. Add tests in `tests/api/test_routes.py`
4. Update this documentation

---

## License

Part of the AI Chat Web Interface project.
