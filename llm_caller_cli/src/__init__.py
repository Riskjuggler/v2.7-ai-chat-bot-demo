"""LLM Caller - Centralized AI inference service for modular tool ecosystem."""

from .core.llm_service import LLMService, chat, embed
from .models.request_models import (
    TaskType,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    HealthStatus,
    MetricsData
)
from .config.settings import get_config, reload_config, LLMCallerConfig
from .providers.base_provider import ProviderAdapter, ProviderError

__version__ = "1.0.0"
__author__ = "AI Assistant Project Team"

# Public API exports
__all__ = [
    # Main service class
    "LLMService",

    # Convenience functions
    "chat",
    "embed",

    # Request/Response models
    "TaskType",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "CompletionRequest",
    "CompletionResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "ModelInfo",
    "HealthStatus",
    "MetricsData",

    # Configuration
    "get_config",
    "reload_config",
    "LLMCallerConfig",

    # Provider interfaces
    "ProviderAdapter",
    "ProviderError"
]