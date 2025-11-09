# AI Chat Web Interface

A modern, production-ready web application for conversing with AI language models. Features a clean React frontend and FastAPI backend with support for multiple LLM providers (OpenAI, Anthropic, and local models via LM Studio).

## Features

- **Multiple LLM Providers**: Seamless integration with OpenAI, Anthropic (Claude), and local models via LM Studio
- **Intelligent Model Routing**: Automatic selection of the best model for your task
- **Modern Chat Interface**: Clean, responsive React UI with real-time streaming
- **Security First**: Localhost-only API access by default, secure credential management
- **Full Test Coverage**: Comprehensive unit, integration, and end-to-end tests
- **Easy Setup**: Simple startup scripts to get running in under 5 minutes

## Quick Start

Get up and running in less than 5 minutes:

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd v2.7-test
   ```

2. **Configure API keys**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API key for at least one provider
   ```

3. **Start the application**:
   ```bash
   # On Unix/Mac:
   ./scripts/start-all.sh

   # On Windows:
   scripts\start-all.bat
   ```

4. **Open your browser** to http://localhost:3000 and start chatting!

See [Quick Start Guide](docs/QUICK_START.md) for detailed instructions.

## Prerequisites

- **Python 3.9+** (backend)
- **Node.js 18+** (frontend)
- **LM Studio** (optional, for local models) - Download from [lmstudio.ai](https://lmstudio.ai/)
- **API Keys** (at least one):
  - OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys)
  - Anthropic API key from [console.anthropic.com](https://console.anthropic.com/)
  - OR LM Studio with loaded models (no API key needed)

## Installation

### Backend Setup

1. **Create Python virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your provider credentials (see Configuration section)
   ```

### Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

2. **Build for production** (optional):
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

## Configuration

Edit `.env` file to configure your LLM providers:

### Option A: Cloud Providers (OpenAI/Anthropic)

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

### Option B: Local Models (LM Studio)

```bash
# LM Studio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LLM_CALLER_PREFER_LOCAL=true
```

1. Install LM Studio from [lmstudio.ai](https://lmstudio.ai/)
2. Load one or more models (e.g., Llama, Mistral, CodeLlama)
3. Start the local server in LM Studio
4. Models are auto-discovered via the `/v1/models` API

### Option C: Hybrid (Best of Both)

Configure both cloud and local providers. The system will use local models when available and fall back to cloud providers.

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LLM_CALLER_PREFER_LOCAL=true  # Prefer local models for privacy
```

See `.env.example` for all configuration options.

## Running the Application

### Using Startup Scripts (Recommended)

**Unix/Mac:**
```bash
# Start both backend and frontend
./scripts/start-all.sh

# Or start separately:
./scripts/start-backend.sh  # Starts on http://localhost:8000
./scripts/start-frontend.sh # Starts on http://localhost:3000
```

**Windows:**
```bash
# Start both backend and frontend
scripts\start-all.bat

# Or start separately:
scripts\start-backend.bat  # Starts on http://localhost:8000
scripts\start-frontend.bat # Starts on http://localhost:3000
```

### Manual Startup

**Backend:**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Accessing the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## Testing

### Run All Tests

```bash
# Backend tests (unit + integration)
pytest tests/ -v --cov=src --cov-report=term-missing

# Frontend tests
cd frontend && npm test && cd ..

# End-to-end tests
pytest e2e/ -v
```

### Run Specific Test Suites

```bash
# Backend unit tests only
pytest tests/ -v -m unit

# Backend integration tests only
pytest tests/ -v -m integration

# Frontend tests with coverage
cd frontend && npm test -- --coverage && cd ..
```

### Test Coverage

Current test coverage:
- **Backend**: >90% (unit and integration tests)
- **Frontend**: >80% (component and service tests)
- **E2E**: Full user journey coverage

Generate coverage reports:
```bash
# Backend coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Frontend coverage report
cd frontend && npm test -- --coverage && cd ..
```

## Project Structure

```
v2.7-test/
├── src/api/                 # FastAPI backend
│   ├── main.py              # FastAPI app setup
│   ├── routes.py            # API endpoints
│   ├── models.py            # Data models
│   ├── llm_service.py       # LLM integration
│   ├── middleware.py        # Security middleware
│   └── config.py            # Configuration
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API client services
│   │   ├── types/           # TypeScript types
│   │   └── App.tsx          # Main app component
│   └── package.json
├── llm_caller_cli/          # LLM integration module
│   ├── src/
│   │   ├── core/            # Core LLM caller logic
│   │   ├── providers/       # Provider implementations
│   │   ├── config/          # Configuration management
│   │   └── models/          # Data models
│   └── tests/               # Module tests (241 tests)
├── tests/                   # Backend tests
│   ├── test_api.py          # API endpoint tests
│   ├── test_llm_service.py  # Service layer tests
│   └── test_integration.py  # Integration tests
├── e2e/                     # End-to-end tests
│   └── test_chat_flow.py    # Full chat flow tests
├── docs/                    # Documentation
│   ├── API.md               # API documentation
│   ├── TESTING.md           # Testing guide
│   ├── INTEGRATION.md       # Integration guide
│   ├── QUICK_START.md       # Quick start guide
│   ├── ARCHITECTURE.md      # Architecture documentation
│   └── DEPLOYMENT.md        # Deployment guide
├── scripts/                 # Startup scripts
│   ├── start-backend.sh     # Start backend (Unix)
│   ├── start-frontend.sh    # Start frontend (Unix)
│   ├── start-all.sh         # Start both (Unix)
│   └── *.bat                # Windows equivalents
├── .env.example             # Environment configuration template
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Architecture

The application uses a modern client-server architecture:

- **Frontend**: React 18 with TypeScript, Vite build tool
- **Backend**: FastAPI (Python 3.9+) with async support
- **LLM Integration**: Unified interface for multiple providers
- **Security**: Localhost-only middleware, CORS protection
- **Testing**: Pytest (backend), Vitest (frontend), Playwright (E2E)

See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed design decisions and patterns.

## API Documentation

Interactive API documentation is available at http://localhost:8000/docs when the backend is running.

Key endpoints:
- `POST /chat` - Send chat message and receive AI response
- `GET /models` - List available models
- `GET /health` - Health check

See [API Documentation](docs/API.md) for complete API reference.

## Troubleshooting

### Backend won't start

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend won't start

**Problem**: `Cannot find module` or build errors

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API returns 401 or 403 errors

**Problem**: API key not configured or invalid

**Solution**:
```bash
# Check .env file exists and has valid API key
cat .env | grep API_KEY

# Validate configuration
python llm_cli.py config --validate
```

### LM Studio models not detected

**Problem**: No models appear when using LM Studio

**Solution**:
1. Ensure LM Studio is running with local server started
2. Load at least one model in LM Studio
3. Verify `LMSTUDIO_BASE_URL=http://localhost:1234/v1` in `.env`
4. Test connection: `curl http://localhost:1234/v1/models`

### Port already in use

**Problem**: `Address already in use` error

**Solution**:
```bash
# Find process using port 8000 (backend)
lsof -i :8000  # On Unix/Mac
netstat -ano | findstr :8000  # On Windows

# Kill the process or use a different port:
uvicorn src.api.main:app --port 8001
```

### CORS errors in browser

**Problem**: Cross-origin request blocked

**Solution**: Ensure frontend URL matches CORS configuration in `src/api/main.py`:
```python
allow_origins=[
    "http://localhost:3000",  # Default
    "http://localhost:5173",  # Vite default
]
```

### Tests failing

**Problem**: Tests fail with import or module errors

**Solution**:
```bash
# Ensure pytest is installed in virtual environment
pip install -r requirements.txt

# Run with verbose output to see errors
pytest tests/ -v -s
```

For more troubleshooting help, see [Testing Guide](docs/TESTING.md) and [Integration Guide](docs/INTEGRATION.md).

## Development

### Code Style

The project uses:
- **Python**: Black formatter, Ruff linter
- **TypeScript**: ESLint, Prettier
- **Pre-commit hooks**: Automatic formatting and linting

### Adding New Features

1. Create a new branch
2. Implement feature with tests
3. Run all test suites
4. Ensure linting passes
5. Submit pull request

### Running Linters

```bash
# Python
ruff check src/ tests/
black src/ tests/

# TypeScript
cd frontend && npm run lint && cd ..
```

## Security

- **Localhost-only**: API only accepts requests from localhost by default
- **No credentials in code**: All API keys in `.env` (gitignored)
- **CORS protection**: Strict origin validation
- **Input validation**: All API inputs validated with Pydantic
- **Secure dependencies**: Regular dependency updates and security scanning

See [Security Audit](SECURITY_AUDIT.md) for detailed security analysis.

## Performance

- **Backend**: FastAPI async handlers for concurrent requests
- **Frontend**: React 18 with concurrent rendering
- **Streaming**: Real-time response streaming for long completions
- **Caching**: Model metadata caching to reduce API calls

See [Performance Results](PERFORMANCE_RESULTS.md) for benchmark data.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add license information here]

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [documentation](docs/)
- Open an issue on GitHub

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
- [LM Studio](https://lmstudio.ai/) - Local model hosting
- [OpenAI API](https://platform.openai.com/) - Cloud LLM provider
- [Anthropic API](https://www.anthropic.com/) - Claude AI provider

---

**Version**: 0.1.0
**Status**: Production Ready
**Last Updated**: 2025-11-09
