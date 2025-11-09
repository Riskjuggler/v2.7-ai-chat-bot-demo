"""Main LLM service for orchestrating providers and routing requests."""

import time
import logging
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any
from ..models.request_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    HealthStatus,
    ProviderStatus,
    MetricsData,
    StreamChunk,
    TaskType
)
from ..providers.base_provider import ProviderAdapter, ProviderError
from ..providers.lmstudio_provider import LMStudioProvider
from ..core.routing_engine import RoutingEngine
from ..config.settings import LLMCallerConfig, get_config
from ..config.model_capabilities import ModelCapability, ModelCategory


logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages provider instances and their lifecycle."""

    def __init__(self, config: LLMCallerConfig):
        """Initialize provider manager.

        Args:
            config: LLM Caller configuration
        """
        self.config = config
        self.providers: Dict[str, ProviderAdapter] = {}
        self._provider_health: Dict[str, ProviderStatus] = {}
        self._initialization_lock = asyncio.Lock()

    async def initialize_providers(self):
        """Initialize all enabled providers."""
        async with self._initialization_lock:
            for provider_name, provider_config in self.config.providers.items():
                if provider_config.enabled and provider_name not in self.providers:
                    try:
                        provider = await self._create_provider(provider_name, provider_config.model_dump())
                        self.providers[provider_name] = provider
                        logger.info(f"Initialized provider: {provider_name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize provider {provider_name}: {e}")

    async def _create_provider(self, provider_name: str, config: Dict[str, Any]) -> ProviderAdapter:
        """Create provider instance.

        Args:
            provider_name: Name of the provider
            config: Provider configuration

        Returns:
            Provider adapter instance
        """
        if provider_name == "lmstudio":
            provider = LMStudioProvider(config)
        elif provider_name == "openai":
            # Import here to avoid dependency issues if not installed
            try:
                from ..providers.openai_provider import OpenAIProvider
                provider = OpenAIProvider(config)
            except ImportError:
                raise ImportError("OpenAI provider requires 'openai' package. Install with: pip install openai")
        elif provider_name == "anthropic":
            # Import here to avoid dependency issues if not installed
            try:
                from ..providers.anthropic_provider import AnthropicProvider
                provider = AnthropicProvider(config)
            except ImportError:
                raise ImportError("Anthropic provider requires 'anthropic' package. Install with: pip install anthropic")
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

        await provider.initialize()
        return provider

    async def get_provider(self, provider_name: str) -> Optional[ProviderAdapter]:
        """Get provider instance.

        Args:
            provider_name: Provider name

        Returns:
            Provider instance or None if not available
        """
        return self.providers.get(provider_name)

    async def get_available_providers(self) -> List[str]:
        """Get list of available provider names.

        Returns:
            List of available provider names
        """
        available = []
        for provider_name, provider in self.providers.items():
            try:
                status = await provider.health_check()
                if status.status == "online":
                    available.append(provider_name)
            except Exception:
                continue
        return available

    async def cleanup(self):
        """Cleanup all providers."""
        for provider in self.providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up provider: {e}")

    async def health_check_all(self) -> Dict[str, ProviderStatus]:
        """Perform health check on all providers.

        Returns:
            Dictionary of provider health statuses
        """
        health_results = {}
        for provider_name, provider in self.providers.items():
            try:
                status = await provider.health_check()
                health_results[provider_name] = status
            except Exception as e:
                health_results[provider_name] = ProviderStatus(
                    name=provider_name,
                    status="error",
                    models_available=[],
                    error_message=str(e),
                    last_check=int(time.time())
                )
        return health_results


class LLMService:
    """Main LLM service for handling requests and routing to providers."""

    def __init__(self, config: Optional[LLMCallerConfig] = None):
        """Initialize LLM service.

        Args:
            config: Optional configuration, will load from file if not provided
        """
        self.config = config or get_config()
        self.provider_manager = ProviderManager(self.config)
        self.routing_engine = RoutingEngine()
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "provider_requests": {},
            "model_requests": {},
            "task_requests": {}
        }
        self._start_time = time.time()

    async def initialize(self):
        """Initialize the LLM service."""
        await self.provider_manager.initialize_providers()

        # Dynamically register models from providers
        await self._register_provider_models()

        logger.info("LLM service initialized successfully")

    async def _register_provider_models(self):
        """Discover and register models from all providers."""
        for provider_name, provider in self.provider_manager.providers.items():
            try:
                # Get models from provider
                models = await provider.list_models()

                for model in models:
                    # Infer model capabilities
                    supported_tasks = self._infer_supported_tasks(model.id)

                    # Skip embedding models (they don't support chat/completion tasks)
                    if not supported_tasks:
                        logger.debug(f"Skipping embedding model: {model.id}")
                        continue

                    # Create capability for discovered model
                    capability = ModelCapability(
                        model_id=model.id,
                        provider=provider_name,
                        category=self._infer_model_category(model.id),
                        supported_tasks=supported_tasks,
                        context_length=provider.get_context_length(model.id) or 4096,
                        quality_score=0.7,  # Default score
                        speed_score=0.8,    # Default score for local models
                        supports_functions=provider.supports_functions(),
                        max_output_tokens=2048,
                        description=model.description or f"{model.id} from {provider_name}"
                    )
                    # Register capability (replaces existing if present)
                    self.routing_engine.capability_registry._capabilities[model.id] = capability
                    logger.info(f"Dynamically registered model: {model.id} from {provider_name}")

            except Exception as e:
                logger.warning(f"Could not register models from {provider_name}: {e}")

    def _infer_model_category(self, model_id: str) -> ModelCategory:
        """Infer model category from model ID."""
        model_lower = model_id.lower()

        if any(term in model_lower for term in ['code', 'deepseek-coder', 'codellama', 'starcoder']):
            return ModelCategory.CODE_SPECIALIZED
        elif 'gpt-4' in model_lower or 'claude-3-opus' in model_lower:
            return ModelCategory.ADVANCED_REASONING
        elif 'embed' in model_lower:
            return ModelCategory.EMBEDDING
        else:
            return ModelCategory.LOCAL

    def _infer_supported_tasks(self, model_id: str) -> set:
        """Infer supported tasks from model ID."""
        from ..models.request_models import TaskType

        model_lower = model_id.lower()

        # Embedding models don't support chat/completion tasks
        if 'embed' in model_lower or 'embedding' in model_lower:
            return set()  # No chat tasks supported

        # All non-embedding models support general tasks
        tasks = {TaskType.GENERAL}

        if any(term in model_lower for term in ['code', 'deepseek-coder', 'codellama', 'starcoder']):
            tasks.update({
                TaskType.CODE_ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.CODE_REVIEW
            })

        if 'llama' in model_lower or 'mistral' in model_lower or 'qwen' in model_lower:
            tasks.update({
                TaskType.CREATIVE_WRITING,
                TaskType.DOCUMENT_SUMMARY,
                TaskType.TRANSLATION
            })

        if 'gpt-4' in model_lower or 'claude' in model_lower:
            tasks.update({
                TaskType.CODE_ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.DOCUMENT_ANALYSIS,
                TaskType.DOCUMENT_SUMMARY,
                TaskType.TECHNICAL_WRITING,
                TaskType.DATA_ANALYSIS,
                TaskType.MATH_REASONING,
                TaskType.SCIENTIFIC_ANALYSIS
            })

        return tasks

    async def cleanup(self):
        """Cleanup the LLM service."""
        await self.provider_manager.cleanup()
        logger.info("LLM service cleaned up")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        prefer_local: bool = False,
        **kwargs
    ) -> ChatCompletionResponse:
        """Generate chat completion.

        Args:
            messages: Chat messages
            model: Optional specific model to use
            task_type: Optional task type for routing
            prefer_local: Prefer local models
            **kwargs: Additional parameters

        Returns:
            Chat completion response
        """
        from ..models.request_models import ChatMessage, MessageRole

        # Convert messages to proper format
        chat_messages = [
            ChatMessage(role=MessageRole(msg["role"]), content=msg["content"])
            for msg in messages
        ]

        request = ChatCompletionRequest(
            messages=chat_messages,
            model=model,
            task_type=task_type,
            prefer_local=prefer_local,
            **kwargs
        )

        # Increment metrics before handling request
        self._metrics["total_requests"] += 1

        try:
            response = await self._handle_chat_completion(request)
            self._metrics["successful_requests"] += 1
            return response
        except Exception as e:
            self._metrics["failed_requests"] += 1
            raise

    async def _handle_chat_completion(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Handle chat completion request with routing and fallback.

        Args:
            request: Chat completion request

        Returns:
            Chat completion response
        """
        start_time = time.time()

        try:
            # Get available providers
            available_providers = await self.provider_manager.get_available_providers()
            if not available_providers:
                raise ProviderError("No providers available", "service")

            # Route request to best model
            routing_decision = self.routing_engine.route_chat_completion(
                request, available_providers
            )

            # Track metrics
            self._update_metrics(routing_decision.selected_provider, routing_decision.selected_model, routing_decision.task_type)

            # Get provider and make request
            provider = await self.provider_manager.get_provider(routing_decision.selected_provider)
            if not provider:
                raise ProviderError(f"Provider {routing_decision.selected_provider} not available", "service")

            # Update request with selected model
            request.model = routing_decision.selected_model

            response = await provider.chat_completion(request)

            # Update response with routing info
            response.provider = routing_decision.selected_provider

            logger.info(f"Chat completion successful: {routing_decision.selected_model} ({time.time() - start_time:.2f}s)")

            return response

        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        prefer_local: bool = False,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate streaming chat completion.

        Args:
            messages: Chat messages
            model: Optional specific model to use
            task_type: Optional task type for routing
            prefer_local: Prefer local models
            **kwargs: Additional parameters

        Yields:
            Stream chunks
        """
        from ..models.request_models import ChatMessage, MessageRole

        # Convert messages to proper format
        chat_messages = [
            ChatMessage(role=MessageRole(msg["role"]), content=msg["content"])
            for msg in messages
        ]

        request = ChatCompletionRequest(
            messages=chat_messages,
            model=model,
            task_type=task_type,
            prefer_local=prefer_local,
            stream=True,
            **kwargs
        )

        async for chunk in self._handle_chat_completion_stream(request):
            yield chunk

    async def _handle_chat_completion_stream(
        self,
        request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Handle streaming chat completion request.

        Args:
            request: Chat completion request

        Yields:
            Stream chunks
        """
        self._metrics["total_requests"] += 1

        try:
            # Get available providers
            available_providers = await self.provider_manager.get_available_providers()
            if not available_providers:
                raise ProviderError("No providers available", "service")

            # Route request to best model
            routing_decision = self.routing_engine.route_chat_completion(
                request, available_providers
            )

            # Track metrics
            self._update_metrics(routing_decision.selected_provider, routing_decision.selected_model, routing_decision.task_type)

            # Get provider and make request
            provider = await self.provider_manager.get_provider(routing_decision.selected_provider)
            if not provider:
                raise ProviderError(f"Provider {routing_decision.selected_provider} not available", "service")

            # Update request with selected model
            request.model = routing_decision.selected_model

            async for chunk in provider.chat_completion_stream(request):
                chunk.provider = routing_decision.selected_provider
                yield chunk

            self._metrics["successful_requests"] += 1

        except Exception as e:
            self._metrics["failed_requests"] += 1
            logger.error(f"Streaming chat completion failed: {e}")
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> EmbeddingResponse:
        """Generate embeddings.

        Args:
            texts: List of texts to embed
            model: Optional specific model to use

        Returns:
            Embedding response
        """
        request = EmbeddingRequest(
            input=texts,
            model=model
        )

        self._metrics["total_requests"] += 1

        try:
            # Get available providers
            available_providers = await self.provider_manager.get_available_providers()
            if not available_providers:
                raise ProviderError("No providers available", "service")

            # Route request to best embedding model
            routing_decision = self.routing_engine.route_embedding(
                request, available_providers
            )

            # Track metrics
            self._update_metrics(routing_decision.selected_provider, routing_decision.selected_model, TaskType.DOCUMENT_ANALYSIS)

            # Get provider and make request
            provider = await self.provider_manager.get_provider(routing_decision.selected_provider)
            if not provider:
                raise ProviderError(f"Provider {routing_decision.selected_provider} not available", "service")

            # Update request with selected model
            request.model = routing_decision.selected_model

            response = await provider.generate_embeddings(request)

            # Update response with routing info
            response.provider = routing_decision.selected_provider

            self._metrics["successful_requests"] += 1
            logger.info(f"Embedding generation successful: {routing_decision.selected_model}")

            return response

        except Exception as e:
            self._metrics["failed_requests"] += 1
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def list_models(self) -> List[ModelInfo]:
        """List all available models across providers.

        Returns:
            List of available models
        """
        all_models = []
        for provider_name, provider in self.provider_manager.providers.items():
            try:
                models = await provider.list_models()
                all_models.extend(models)
            except Exception as e:
                logger.warning(f"Failed to list models from {provider_name}: {e}")

        return all_models

    async def health_check(self) -> HealthStatus:
        """Get service health status.

        Returns:
            Service health status
        """
        provider_health = await self.provider_manager.health_check_all()

        # Determine overall status
        online_providers = sum(1 for status in provider_health.values() if status.status == "online")
        total_providers = len(provider_health)

        if online_providers == 0:
            overall_status = "unhealthy"
        elif online_providers < total_providers:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        # Count available models
        total_models = sum(len(status.models_available) for status in provider_health.values())

        return HealthStatus(
            status=overall_status,
            timestamp=int(time.time()),
            providers={name: status.model_dump() for name, status in provider_health.items()},
            models_available=total_models,
            uptime_seconds=time.time() - self._start_time
        )

    async def get_metrics(self) -> MetricsData:
        """Get service metrics.

        Returns:
            Service metrics data
        """
        # Calculate average latency (simplified)
        total_requests = self._metrics["total_requests"]
        avg_latency = 1000.0 if total_requests > 0 else 0.0  # Placeholder

        # Convert simple counts to expected dict format
        provider_breakdown = {
            provider: {"requests": count, "errors": 0, "avg_latency_ms": avg_latency}
            for provider, count in self._metrics["provider_requests"].items()
        }

        return MetricsData(
            total_requests=self._metrics["total_requests"],
            successful_requests=self._metrics["successful_requests"],
            failed_requests=self._metrics["failed_requests"],
            average_latency_ms=avg_latency,
            total_tokens_used=0,  # Would need to track from provider responses
            provider_breakdown=provider_breakdown,
            task_breakdown=self._metrics["task_requests"],
            model_breakdown=self._metrics["model_requests"]
        )

    def _update_metrics(self, provider: str, model: str, task_type: TaskType):
        """Update internal metrics.

        Args:
            provider: Provider name
            model: Model name
            task_type: Task type
        """
        # Track by provider
        if provider not in self._metrics["provider_requests"]:
            self._metrics["provider_requests"][provider] = 0
        self._metrics["provider_requests"][provider] += 1

        # Track by model
        if model not in self._metrics["model_requests"]:
            self._metrics["model_requests"][model] = 0
        self._metrics["model_requests"][model] += 1

        # Track by task type
        task_key = task_type.value if task_type else "unknown"
        if task_key not in self._metrics["task_requests"]:
            self._metrics["task_requests"][task_key] = 0
        self._metrics["task_requests"][task_key] += 1

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


# Convenience functions for quick usage
async def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    task_type: Optional[TaskType] = None,
    prefer_local: bool = False,
    **kwargs
) -> ChatCompletionResponse:
    """Quick chat completion function.

    Args:
        messages: Chat messages
        model: Optional specific model to use
        task_type: Optional task type for routing
        prefer_local: Prefer local models
        **kwargs: Additional parameters

    Returns:
        Chat completion response
    """
    async with LLMService() as service:
        return await service.chat_completion(
            messages, model, task_type, prefer_local, **kwargs
        )


async def embed(texts: List[str], model: Optional[str] = None) -> EmbeddingResponse:
    """Quick embedding generation function.

    Args:
        texts: List of texts to embed
        model: Optional specific model to use

    Returns:
        Embedding response
    """
    async with LLMService() as service:
        return await service.generate_embeddings(texts, model)