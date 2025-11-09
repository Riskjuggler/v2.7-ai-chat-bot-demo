"""Base provider adapter interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator, Any
from ..models.request_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderStatus,
    StreamChunk
)


class ProviderAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the provider adapter.

        Args:
            name: Provider name (e.g., 'openai', 'lmstudio')
            config: Provider-specific configuration
        """
        self.name = name
        self.config = config
        self._models_cache: Optional[List[ModelInfo]] = None
        self._last_models_fetch: Optional[float] = None

    @abstractmethod
    async def chat_completion(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Generate chat completion.

        Args:
            request: Chat completion request

        Returns:
            Chat completion response

        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate streaming chat completion.

        Args:
            request: Chat completion request with stream=True

        Yields:
            Stream chunks

        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    async def text_completion(
        self,
        request: CompletionRequest
    ) -> CompletionResponse:
        """Generate text completion.

        Args:
            request: Text completion request

        Returns:
            Text completion response

        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    async def generate_embeddings(
        self,
        request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """Generate embeddings.

        Args:
            request: Embedding request

        Returns:
            Embedding response

        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models.

        Returns:
            List of available models

        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Check provider health status.

        Returns:
            Provider status information

        Raises:
            ProviderError: If the health check fails
        """
        pass

    async def get_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """Get available models with caching.

        Args:
            force_refresh: Force refresh from provider

        Returns:
            List of available models
        """
        import time

        # Cache models for 5 minutes
        if (not force_refresh and
            self._models_cache and
            self._last_models_fetch and
            time.time() - self._last_models_fetch < 300):
            return self._models_cache

        self._models_cache = await self.list_models()
        self._last_models_fetch = time.time()
        return self._models_cache

    def supports_chat(self) -> bool:
        """Check if provider supports chat completions."""
        return True

    def supports_completion(self) -> bool:
        """Check if provider supports text completions."""
        return True

    def supports_embeddings(self) -> bool:
        """Check if provider supports embeddings."""
        return True

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        return True

    def supports_functions(self) -> bool:
        """Check if provider supports function calling."""
        return False

    def get_model_capabilities(self, model_id: str) -> Dict[str, Any]:
        """Get capabilities for a specific model.

        Args:
            model_id: Model identifier

        Returns:
            Model capabilities dictionary
        """
        return {
            "chat": self.supports_chat(),
            "completion": self.supports_completion(),
            "embeddings": self.supports_embeddings(),
            "streaming": self.supports_streaming(),
            "functions": self.supports_functions(),
            "context_length": self.get_context_length(model_id),
            "input_cost_per_token": None,
            "output_cost_per_token": None
        }

    def get_context_length(self, model_id: str) -> Optional[int]:
        """Get context length for a model.

        Args:
            model_id: Model identifier

        Returns:
            Context length in tokens, None if unknown
        """
        return None

    def estimate_tokens(self, text: str, model_id: str) -> int:
        """Estimate token count for text.

        Args:
            text: Input text
            model_id: Model identifier

        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4

    def validate_request(self, request: Any) -> bool:
        """Validate a request against provider capabilities.

        Args:
            request: Request object to validate

        Returns:
            True if request is valid

        Raises:
            ValueError: If request is invalid
        """
        return True

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self):
        """Initialize provider resources."""
        pass

    async def cleanup(self):
        """Cleanup provider resources."""
        pass


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        """Initialize provider error.

        Args:
            message: Error message
            provider: Provider name
            error_code: Optional error code
        """
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code


class ProviderTimeoutError(ProviderError):
    """Provider timeout error."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Provider authentication error."""
    pass


class ProviderRateLimitError(ProviderError):
    """Provider rate limit error."""

    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        """Initialize rate limit error.

        Args:
            message: Error message
            provider: Provider name
            retry_after: Seconds to wait before retry
        """
        super().__init__(message, provider, "rate_limit")
        self.retry_after = retry_after


class ProviderQuotaExceededError(ProviderError):
    """Provider quota exceeded error."""
    pass


class ProviderModelNotFoundError(ProviderError):
    """Provider model not found error."""
    pass


class ProviderConnectionError(ProviderError):
    """Provider connection error."""
    pass


class ProviderInvalidRequestError(ProviderError):
    """Provider invalid request error."""
    pass