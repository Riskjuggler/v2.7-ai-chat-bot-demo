"""
TDD Tests for LLMService core functionality.

These tests are written FIRST to drive the implementation and design.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from llm_caller_cli.src.core.llm_service import LLMService, ProviderManager
from llm_caller_cli.src.models.request_models import (
    TaskType,
    ChatCompletionResponse,
    EmbeddingResponse,
    HealthStatus,
    MetricsData,
    ModelInfo,
    Choice,
    ChatMessage,
    MessageRole
)
from llm_caller_cli.src.providers.base_provider import ProviderError


def create_mock_chat_response(content: str, model: str = "gpt-4", provider: str = "openai") -> ChatCompletionResponse:
    """Helper to create properly structured ChatCompletionResponse."""
    choice = Choice(
        index=0,
        message=ChatMessage(role=MessageRole.ASSISTANT, content=content),
        finish_reason="stop"
    )
    return ChatCompletionResponse(
        id="test-123",
        created=1234567890,
        model=model,
        provider=provider,
        choices=[choice]
    )


class TestLLMServiceInitialization:
    """Test LLMService initialization and lifecycle."""

    @pytest.mark.asyncio
    async def test_service_initializes_with_default_config(self):
        """Test that service initializes with default configuration."""
        service = LLMService()

        # Should have provider manager and routing engine
        assert service.provider_manager is not None
        assert service.routing_engine is not None
        assert service.config is not None

        # Should initialize metrics
        assert service._metrics["total_requests"] == 0
        assert service._metrics["successful_requests"] == 0
        assert service._metrics["failed_requests"] == 0

    @pytest.mark.asyncio
    async def test_service_initializes_with_custom_config(self):
        """Test that service can be initialized with custom config."""
        from src.config.settings import LLMCallerConfig

        custom_config = LLMCallerConfig(
            host="custom-host",
            port=9999,
            debug=True
        )

        service = LLMService(config=custom_config)

        assert service.config.host == "custom-host"
        assert service.config.port == 9999
        assert service.config.debug is True

    @pytest.mark.asyncio
    async def test_service_initialize_sets_up_providers(self):
        """Test that initialize() properly sets up all providers."""
        service = LLMService()

        with patch.object(service.provider_manager, 'initialize_providers') as mock_init:
            await service.initialize()
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_cleanup_cleans_providers(self):
        """Test that cleanup() properly cleans up all providers."""
        service = LLMService()

        with patch.object(service.provider_manager, 'cleanup') as mock_cleanup:
            await service.cleanup()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_context_manager_lifecycle(self):
        """Test that service works as async context manager."""
        with patch('llm_caller_cli.src.core.llm_service.LLMService.initialize') as mock_init, \
             patch('llm_caller_cli.src.core.llm_service.LLMService.cleanup') as mock_cleanup:

            async with LLMService() as service:
                assert service is not None
                mock_init.assert_called_once()

            mock_cleanup.assert_called_once()


class TestLLMServiceChatCompletion:
    """Test chat completion functionality."""

    @pytest.mark.asyncio
    async def test_chat_completion_with_simple_message(self):
        """Test basic chat completion with single message."""
        service = LLMService()

        # Mock the internal handler
        from models.request_models import Choice, ChatMessage, MessageRole
        mock_choice = Choice(
            index=0,
            message=ChatMessage(role=MessageRole.ASSISTANT, content="Hello! How can I help you?"),
            finish_reason="stop"
        )
        mock_response = ChatCompletionResponse(
            id="test-123",
            created=1234567890,
            model="gpt-4",
            provider="openai",
            choices=[mock_choice]
        )

        with patch.object(service, '_handle_chat_completion', return_value=mock_response) as mock_handler:
            response = await service.chat_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )

            # Verify response
            assert response.id == "test-123"
            assert response.model == "gpt-4"
            assert response.provider == "openai"

            # Verify handler was called with correct request
            mock_handler.assert_called_once()
            request = mock_handler.call_args[0][0]
            assert len(request.messages) == 1
            assert request.messages[0].content == "Hello"
            assert request.messages[0].role.value == "user"

    @pytest.mark.asyncio
    async def test_chat_completion_with_task_type(self):
        """Test chat completion with explicit task type."""
        service = LLMService()

        mock_response = create_mock_chat_response(
            "def fibonacci(n): ...",
            model="codellama-7b",
            provider="lmstudio"
        )

        with patch.object(service, '_handle_chat_completion', return_value=mock_response):
            response = await service.chat_completion(
                messages=[{"role": "user", "content": "Write a fibonacci function"}],
                task_type=TaskType.CODE_GENERATION
            )

            assert response.model == "codellama-7b"

    @pytest.mark.asyncio
    async def test_chat_completion_with_model_preference(self):
        """Test chat completion with specific model."""
        service = LLMService()

        mock_response = create_mock_chat_response("Response")

        with patch.object(service, '_handle_chat_completion', return_value=mock_response) as mock_handler:
            await service.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="gpt-4"
            )

            request = mock_handler.call_args[0][0]
            assert request.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_chat_completion_with_local_preference(self):
        """Test chat completion with local model preference."""
        service = LLMService()

        mock_response = create_mock_chat_response(
            "Response",
            model="llama-2-7b",
            provider="lmstudio"
        )

        with patch.object(service, '_handle_chat_completion', return_value=mock_response) as mock_handler:
            await service.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                prefer_local=True
            )

            request = mock_handler.call_args[0][0]
            assert request.prefer_local is True

    @pytest.mark.asyncio
    async def test_chat_completion_updates_metrics_on_success(self):
        """Test that successful chat completion updates metrics."""
        service = LLMService()

        mock_response = create_mock_chat_response("Response")

        # Mock the dependencies instead of the internal handler
        with patch.object(service.provider_manager, 'get_available_providers', return_value=["openai"]), \
             patch.object(service.routing_engine, 'route_chat_completion') as mock_route, \
             patch.object(service.provider_manager, 'get_provider') as mock_get_provider:

            # Setup routing decision
            from models.request_models import RoutingDecision
            mock_route.return_value = RoutingDecision(
                selected_model="gpt-4",
                selected_provider="openai",
                reasoning="Test routing",
                task_type=TaskType.GENERAL,
                confidence_score=0.9
            )

            # Setup provider
            mock_provider = AsyncMock()
            mock_provider.chat_completion.return_value = mock_response
            mock_get_provider.return_value = mock_provider

            await service.chat_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )

            assert service._metrics["total_requests"] == 1
            assert service._metrics["successful_requests"] == 1
            assert service._metrics["failed_requests"] == 0

    @pytest.mark.asyncio
    async def test_chat_completion_updates_metrics_on_failure(self):
        """Test that failed chat completion updates metrics."""
        service = LLMService()

        # Mock to simulate failure
        with patch.object(service.provider_manager, 'get_available_providers', return_value=[]):
            with pytest.raises(ProviderError):
                await service.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )

            assert service._metrics["total_requests"] == 1
            assert service._metrics["successful_requests"] == 0
            assert service._metrics["failed_requests"] == 1

    @pytest.mark.asyncio
    async def test_chat_completion_handles_no_providers_available(self):
        """Test chat completion when no providers are available."""
        service = LLMService()

        with patch.object(service.provider_manager, 'get_available_providers', return_value=[]):
            with pytest.raises(ProviderError, match="No providers available"):
                await service.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )


class TestLLMServiceStreamingChat:
    """Test streaming chat completion functionality."""

    @pytest.mark.asyncio
    async def test_chat_completion_stream_yields_chunks(self):
        """Test that streaming chat completion yields chunks."""
        service = LLMService()

        # Mock streaming chunks
        async def mock_stream():
            from models.request_models import StreamChunk
            yield StreamChunk(
                id="test-1",
                created=1234567890,
                model="gpt-4",
                provider="openai",
                choices=[{"delta": {"content": "Hello"}}]
            )
            yield StreamChunk(
                id="test-2",
                created=1234567890,
                model="gpt-4",
                provider="openai",
                choices=[{"delta": {"content": " world"}}]
            )

        with patch.object(service, '_handle_chat_completion_stream', return_value=mock_stream()):
            chunks = []
            async for chunk in service.chat_completion_stream(
                messages=[{"role": "user", "content": "Hello"}]
            ):
                chunks.append(chunk)

            assert len(chunks) == 2
            assert chunks[0].choices[0]["delta"]["content"] == "Hello"
            assert chunks[1].choices[0]["delta"]["content"] == " world"


class TestLLMServiceEmbeddings:
    """Test embedding generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_embeddings_single_text(self):
        """Test generating embeddings for single text."""
        service = LLMService()

        from models.request_models import EmbeddingData
        mock_response = EmbeddingResponse(
            data=[EmbeddingData(embedding=[0.1, 0.2, 0.3], index=0)],
            model="text-embedding-ada-002",
            provider="openai"
        )

        with patch.object(service.provider_manager, 'get_available_providers', return_value=["openai"]), \
             patch.object(service.routing_engine, 'route_embedding') as mock_route, \
             patch.object(service.provider_manager, 'get_provider') as mock_get_provider:

            # Setup mocks
            mock_route.return_value = Mock(
                selected_model="text-embedding-ada-002",
                selected_provider="openai"
            )
            mock_provider = AsyncMock()
            mock_provider.generate_embeddings.return_value = mock_response
            mock_get_provider.return_value = mock_provider

            response = await service.generate_embeddings(["Hello world"])

            assert response.model == "text-embedding-ada-002"
            assert response.provider == "openai"
            assert len(response.data) == 1
            assert response.data[0].embedding == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_generate_embeddings_multiple_texts(self):
        """Test generating embeddings for multiple texts."""
        service = LLMService()

        from models.request_models import EmbeddingData
        mock_response = EmbeddingResponse(
            data=[
                EmbeddingData(embedding=[0.1, 0.2, 0.3], index=0),
                EmbeddingData(embedding=[0.4, 0.5, 0.6], index=1)
            ],
            model="text-embedding-ada-002",
            provider="openai"
        )

        with patch.object(service.provider_manager, 'get_available_providers', return_value=["openai"]), \
             patch.object(service.routing_engine, 'route_embedding') as mock_route, \
             patch.object(service.provider_manager, 'get_provider') as mock_get_provider:

            # Setup mocks
            mock_route.return_value = Mock(
                selected_model="text-embedding-ada-002",
                selected_provider="openai"
            )
            mock_provider = AsyncMock()
            mock_provider.generate_embeddings.return_value = mock_response
            mock_get_provider.return_value = mock_provider

            response = await service.generate_embeddings(["Hello", "World"])

            assert len(response.data) == 2
            assert response.data[0].embedding == [0.1, 0.2, 0.3]
            assert response.data[1].embedding == [0.4, 0.5, 0.6]


class TestLLMServiceModelListing:
    """Test model listing functionality."""

    @pytest.mark.asyncio
    async def test_list_models_aggregates_from_all_providers(self):
        """Test that list_models aggregates models from all providers."""
        service = LLMService()

        # Mock providers
        mock_provider1 = AsyncMock()
        mock_provider1.list_models.return_value = [
            ModelInfo(id="gpt-4", provider="openai", owned_by="openai")
        ]

        mock_provider2 = AsyncMock()
        mock_provider2.list_models.return_value = [
            ModelInfo(id="llama-2-7b", provider="lmstudio", owned_by="meta")
        ]

        service.provider_manager.providers = {
            "openai": mock_provider1,
            "lmstudio": mock_provider2
        }

        models = await service.list_models()

        assert len(models) == 2
        model_ids = [model.id for model in models]
        assert "gpt-4" in model_ids
        assert "llama-2-7b" in model_ids

    @pytest.mark.asyncio
    async def test_list_models_handles_provider_failures(self):
        """Test that list_models handles individual provider failures gracefully."""
        service = LLMService()

        # One provider works, one fails
        mock_provider1 = AsyncMock()
        mock_provider1.list_models.return_value = [
            ModelInfo(id="gpt-4", provider="openai", owned_by="openai")
        ]

        mock_provider2 = AsyncMock()
        mock_provider2.list_models.side_effect = Exception("Provider error")

        service.provider_manager.providers = {
            "openai": mock_provider1,
            "lmstudio": mock_provider2
        }

        models = await service.list_models()

        # Should still return models from working provider
        assert len(models) == 1
        assert models[0].id == "gpt-4"


class TestLLMServiceHealthAndMetrics:
    """Test health checking and metrics functionality."""

    @pytest.mark.asyncio
    async def test_health_check_returns_overall_status(self):
        """Test that health_check returns comprehensive health status."""
        service = LLMService()

        # Mock provider health
        from models.request_models import ProviderStatus
        mock_health = {
            "openai": ProviderStatus(
                name="openai",
                status="online",
                models_available=["gpt-4"],
                last_check=1234567890
            ),
            "lmstudio": ProviderStatus(
                name="lmstudio",
                status="offline",
                models_available=[],
                last_check=1234567890
            )
        }

        with patch.object(service.provider_manager, 'health_check_all', return_value=mock_health):
            health = await service.health_check()

            assert health.status == "degraded"  # Some providers offline
            assert health.models_available == 1  # Only from online provider
            assert "openai" in health.providers
            assert "lmstudio" in health.providers

    @pytest.mark.asyncio
    async def test_get_metrics_returns_current_metrics(self):
        """Test that get_metrics returns current service metrics."""
        service = LLMService()

        # Set some test metrics
        service._metrics["total_requests"] = 100
        service._metrics["successful_requests"] = 95
        service._metrics["failed_requests"] = 5
        service._metrics["provider_requests"] = {"openai": 60, "lmstudio": 40}

        metrics = await service.get_metrics()

        assert metrics.total_requests == 100
        assert metrics.successful_requests == 95
        assert metrics.failed_requests == 5
        assert metrics.provider_breakdown["openai"]["requests"] == 60
        assert metrics.provider_breakdown["lmstudio"]["requests"] == 40


class TestLLMServiceRouting:
    """Test request routing functionality."""

    @pytest.mark.asyncio
    async def test_routing_selects_appropriate_provider_for_task(self):
        """Test that routing selects appropriate provider based on task type."""
        service = LLMService()

        # Mock available providers
        with patch.object(service.provider_manager, 'get_available_providers', return_value=["openai", "lmstudio"]):

            # Mock routing decision
            from models.request_models import RoutingDecision
            mock_decision = RoutingDecision(
                selected_model="codellama-7b-instruct",
                selected_provider="lmstudio",
                reasoning="Code generation task routed to specialized model",
                task_type=TaskType.CODE_GENERATION,
                confidence_score=0.95
            )

            with patch.object(service.routing_engine, 'route_chat_completion', return_value=mock_decision):
                # Test routing decision is used
                with patch.object(service.provider_manager, 'get_provider') as mock_get_provider:
                    mock_provider = AsyncMock()
                    mock_provider.chat_completion.return_value = create_mock_chat_response(
                        "def fibonacci(n): ...",
                        model="codellama-7b-instruct",
                        provider="lmstudio"
                    )
                    mock_get_provider.return_value = mock_provider

                    response = await service.chat_completion(
                        messages=[{"role": "user", "content": "Write fibonacci function"}],
                        task_type=TaskType.CODE_GENERATION
                    )

                    # Verify correct provider was selected
                    mock_get_provider.assert_called_with("lmstudio")
                    assert response.model == "codellama-7b-instruct"
                    assert response.provider == "lmstudio"

    @pytest.mark.asyncio
    async def test_routing_updates_provider_and_model_metrics(self):
        """Test that routing updates metrics for provider and model usage."""
        service = LLMService()

        # Mock the internal handler to update metrics
        mock_response = create_mock_chat_response("Response")

        with patch.object(service, '_handle_chat_completion', return_value=mock_response):
            await service.chat_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )

            # Check that metrics tracking was called
            assert service._metrics["total_requests"] == 1
            assert service._metrics["successful_requests"] == 1