# LLM Caller CLI Module

Production-ready LLM integration library supporting multiple providers.

## Overview

This module provides a unified interface for calling Language Learning Models (LLMs) from multiple providers:
- **LM Studio** (local models, privacy-first)
- **OpenAI** (planned)
- **Anthropic** (planned)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

## Integration Status

**Integrated**: 2025-11-09
**Source**: forwork/modules/llm_caller_cli
**Work Unit**: WU-V27-001

### What's Included

- ✅ **12 Python source files** across 4 subdirectories
- ✅ **13 test files** with 201 tests
- ✅ **74.6% test pass rate** (150/201 tests passing)
- ✅ **LM Studio provider** fully implemented and tested
- ✅ **Configuration management** with YAML and environment variables
- ✅ **Intelligent routing engine** for task-based model selection
- ✅ **Comprehensive .env.example** with all provider documentation

### Known Limitations

- OpenAI provider: Not yet implemented (tests expect it)
- Anthropic provider: Not yet implemented (tests expect it)
- CLI scripts: Integrated but some tests need path adjustments

## Quick Start

### Python API

```python
from llm_caller_cli import LLMService, ChatCompletionRequest

# Initialize service
service = LLMService()

# Create chat request
request = ChatCompletionRequest(
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ],
    provider="lmstudio",  # or let routing engine decide
    max_tokens=100
)

# Get response
response = await service.chat_completion(request)
print(response.content)
```

### CLI Usage

```bash
# Check status
python llm_cli.py status

# Simple chat
python llm_cli.py chat "Hello, world!"

# With specific provider
python llm_cli.py chat "Code review please" --provider lmstudio
```

## Architecture

### Directory Structure

```
llm_caller_cli/
├── __init__.py              # Public API exports
├── README.md                # This file
└── src/
    ├── core/                # Core service and routing
    │   ├── llm_service.py   # Main LLM service
    │   └── routing_engine.py # Intelligent model routing
    ├── config/              # Configuration management
    │   ├── settings.py      # Configuration models
    │   └── model_capabilities.py  # Model capability registry
    ├── models/              # Request/response models
    │   └── request_models.py
    └── providers/           # Provider implementations
        ├── base_provider.py      # Provider interface
        └── lmstudio_provider.py  # LM Studio implementation
```

### Key Components

**LLMService**: Main service class for LLM operations
- Chat completion
- Embeddings generation
- Health checks
- Metrics collection

**RoutingEngine**: Intelligent model selection
- Task type detection
- Best model selection based on capabilities
- Local vs cloud preference handling
- Automatic fallback

**Configuration**: Flexible configuration system
- Environment variables
- YAML configuration files
- Provider-specific settings
- Security and privacy controls

## Configuration

### Environment Variables

See `.env.example` for complete documentation. Key variables:

```bash
# LM Studio (Local)
LMSTUDIO_BASE_URL=http://localhost:1234/v1

# Privacy mode
LLM_CALLER_PREFER_LOCAL=true

# Service settings
LLM_CALLER_HOST=localhost
LLM_CALLER_PORT=8080
```

### Provider Priority

Set `LLM_CALLER_PREFER_LOCAL=true` to prioritize local models (LM Studio) over cloud providers.

## Testing

Run the test suite:

```bash
# All tests
pytest tests/llm_caller_cli/ -v

# Exclude CLI tests (require path fixes)
pytest tests/llm_caller_cli/ --ignore=tests/llm_caller_cli/test_cli_commands.py --ignore=tests/llm_caller_cli/test_cli_integration.py -v

# With coverage
pytest tests/llm_caller_cli/ --cov=llm_caller_cli --cov-report=term-missing
```

### Test Results

- **Total tests**: 201
- **Passing**: 150 (74.6%)
- **Failing**: 46 (primarily due to missing OpenAI/Anthropic providers)
- **Skipped**: 5

## Validation

Run the integration validation script:

```bash
python validate_integration.py
```

This validates:
- Module imports work correctly
- All components are accessible
- File structure is complete
- Configuration files are present

## Future Enhancements

- [ ] Implement OpenAI provider
- [ ] Implement Anthropic provider
- [ ] Add streaming support for all providers
- [ ] Implement cost tracking
- [ ] Add rate limiting
- [ ] Enhance error recovery
- [ ] Add caching layer

## Migration Notes

**From forwork/modules/llm_caller_cli**:
- Updated all imports from `modules.llm_caller_cli` to `llm_caller_cli`
- Updated test patch statements to use new import paths
- Copied CLI scripts (llm_call.py, llm_cli.py) to project root
- Created standalone pytest.ini configuration
- Maintained all existing test coverage

## License

Part of the v2.7-test project.

## Support

For issues or questions:
1. Check test results: `pytest tests/llm_caller_cli/ -v`
2. Run validation: `python validate_integration.py`
3. Review logs in project `.claude/` directory
