"""
LLM Caller CLI Module

Production-ready LLM integration library supporting multiple providers:
- OpenAI
- Anthropic
- LM Studio

Integrated into v2.7-test project from forwork/modules/llm_caller_cli.
"""

from llm_caller_cli.src.core.llm_service import LLMService
from llm_caller_cli.src.core.routing_engine import RoutingEngine
from llm_caller_cli.src.config.settings import LLMCallerConfig, get_config
from llm_caller_cli.src.models.request_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    TaskType,
)
from llm_caller_cli.src.providers.base_provider import ProviderAdapter, ProviderError
from llm_caller_cli.src.providers.lmstudio_provider import LMStudioProvider

__all__ = [
    "LLMService",
    "RoutingEngine",
    "LLMCallerConfig",
    "get_config",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "TaskType",
    "ProviderAdapter",
    "ProviderError",
    "LMStudioProvider",
]

__version__ = "1.0.0"
