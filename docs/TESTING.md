# Testing Guide

This document provides instructions for running tests across the AI Chat Web Interface project.

## Test Types

The project includes three levels of testing:

1. **Unit Tests** - Test individual components and services in isolation
2. **End-to-End (E2E) Tests** - Test complete user flows through the application
3. **Manual Tests** - Validate real LLM integration and performance

## Prerequisites

### For All Tests
- Node.js 18+ installed
- Python 3.11+ installed
- Project dependencies installed

### For Manual Tests with LM Studio
- LM Studio installed from https://lmstudio.ai/
- At least one model loaded in LM Studio
- LM Studio local server running on port 1234

## Unit Tests

Unit tests validate individual components and services using Vitest.

### Running Unit Tests

```bash
# Frontend unit tests
cd frontend
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Test Coverage

Unit tests target 100% coverage for:
- API client service (`frontend/src/services/apiClient.ts`)
- React components with integration logic
- Type definitions and utilities

### Writing Unit Tests

Unit tests are located alongside source files with `.test.ts` or `.test.tsx` extension:

```
frontend/src/
  services/
    apiClient.ts
    apiClient.test.ts  ← Unit tests here
  components/
    ChatContainer.tsx
    ChatContainer.test.tsx  ← Component tests here
```

## End-to-End Tests

E2E tests validate complete user flows using Playwright.

### Running E2E Tests

```bash
# Install Playwright (first time only)
npx playwright install

# Run E2E tests (headless)
npm run test:e2e

# Run with UI
npx playwright test --ui

# Run specific test file
npx playwright test e2e/tests/chat.spec.ts

# Run in debug mode
npx playwright test --debug
```

### E2E Test Scenarios

The E2E test suite covers:

**Happy Path:**
- User sends message and receives response
- Multiple messages in sequence
- Auto-scroll to latest message

**Error Scenarios:**
- Backend returns 503 (service unavailable)
- Network failures
- Request timeouts
- Empty message validation

**Loading States:**
- Input disabled during API call
- Loading indicator visibility
- Re-enable after response

**Accessibility:**
- ARIA labels and roles
- Keyboard navigation
- Screen reader support

### Mock LLM Server

E2E tests use a mock LLM server fixture for predictable, fast testing:

```typescript
import { test, expect } from '../fixtures/mockLLM'

test('example', async ({ page, mockLLM }) => {
  await mockLLM({
    response: 'Test response',
    delay: 100, // Optional delay in ms
    shouldFail: false, // Set to true to test error handling
  })

  // Test code...
})
```

## Manual Testing

Manual testing validates real LLM integration and measures performance.

### Setup

1. **Start LM Studio**
   ```bash
   # Open LM Studio application
   # Load a model (e.g., Llama 2, Mistral)
   # Click "Start Server" in LM Studio
   # Verify server is running on http://localhost:1234
   ```

2. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env and set:
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   ```

3. **Start Backend API**
   ```bash
   cd src/api
   python -m uvicorn main:app --reload
   ```

4. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

### Manual Test Checklist

- [ ] Open browser to http://localhost:5173
- [ ] Verify empty state message appears
- [ ] Type a message in the input field
- [ ] Click Send button
- [ ] Verify user message appears in chat
- [ ] Verify loading indicator appears
- [ ] Verify LLM response appears within 3 seconds
- [ ] Send a follow-up message
- [ ] Verify conversation history persists
- [ ] Test error handling (stop LM Studio server, send message)
- [ ] Verify error message displays
- [ ] Restart LM Studio, send message
- [ ] Verify recovery from error

### Performance Testing

Measure response times for typical interactions:

1. **Send 10 messages** of varying lengths (10-200 words)
2. **Record response time** for each (from click to response displayed)
3. **Calculate metrics**:
   - Average response time
   - 90th percentile response time
   - Min/max response times

**Target:** 90% of responses should be <3 seconds for typical messages.

### Performance Test Script

```bash
# Automated performance testing script
python scripts/performance_test.py --messages 10 --output results.json
```

Results are saved to `PERFORMANCE_RESULTS.md`.

## Security Testing

Validate security constraints are enforced.

### Localhost-Only Access

**Test:** Backend API should only respond to localhost requests.

```bash
# From the same machine (should succeed)
curl http://localhost:8000/health
# Response: {"status":"healthy","llm_available":true}

# From another machine or external IP (should fail)
curl http://<external-ip>:8000/health
# Response: Connection refused or timeout
```

### CORS Configuration

**Test:** API should reject requests from unauthorized origins.

```bash
# Test with evil.com origin (should reject)
curl -H "Origin: http://evil.com" http://localhost:8000/chat \
  -X POST -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'

# Should return CORS error or no Access-Control-Allow-Origin header
```

Results are documented in `SECURITY_AUDIT.md`.

## CI/CD Integration

### GitHub Actions

Tests run automatically on every push and pull request:

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: cd frontend && npm test
      - name: Run E2E tests
        run: npx playwright test
```

### Pre-commit Hooks

Install pre-commit hooks to run tests before commit:

```bash
# Install hooks
npm run prepare

# Hooks will run:
# - Linter (ESLint)
# - Type checker (TypeScript)
# - Unit tests
```

## Troubleshooting

### Unit Tests Fail

**Issue:** "Cannot find module '@/types/api'"

**Solution:** Check TypeScript path aliases in `vite.config.ts`:
```typescript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

### E2E Tests Timeout

**Issue:** "Timeout waiting for http://localhost:5173"

**Solution:**
1. Verify frontend starts successfully: `cd frontend && npm run dev`
2. Check port 5173 is not in use: `lsof -i :5173`
3. Increase timeout in `playwright.config.ts`: `timeout: 60000`

### Mock LLM Not Working

**Issue:** E2E tests call real backend instead of mock

**Solution:** Verify route interception in test:
```typescript
await mockLLM({ response: 'Test' })  // Must be called BEFORE page.goto()
await page.goto('/')
```

### Manual Test: LM Studio Connection Fails

**Issue:** "Connection refused" when calling backend

**Solution:**
1. Verify LM Studio server is running: Check UI shows "Server Running"
2. Test LM Studio directly: `curl http://localhost:1234/v1/models`
3. Check .env has correct base URL: `LMSTUDIO_BASE_URL=http://localhost:1234/v1`
4. Restart backend: `uvicorn main:app --reload`

## Test Metrics

### Current Coverage

- **Unit Tests:** 100% coverage for integration code
- **E2E Tests:** 15 test cases covering all critical flows
- **Manual Tests:** Checklist of 12 scenarios

### Quality Gates

Before merging to main:
- [ ] All unit tests pass
- [ ] All E2E tests pass
- [ ] Manual LM Studio test successful
- [ ] Performance target met (<3s for 90% of requests)
- [ ] Security tests pass

## References

- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Library Best Practices](https://testing-library.com/docs/guiding-principles/)
