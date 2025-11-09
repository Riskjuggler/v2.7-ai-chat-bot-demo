"""Simple integration tests for LLM Caller workflows.

This module tests essential end-to-end workflows following TDD principles.
"""

import pytest
import os
from unittest.mock import AsyncMock, patch
from llm_caller_cli.src.core.llm_service import LLMService
from llm_caller_cli.src.models.request_models import (
    ChatMessage,
    MessageRole,
    TaskType,
    Choice,
    ChatCompletionResponse,
    ProviderStatus
)
from llm_caller_cli.src.config.settings import LLMCallerConfig, ProviderConfig


def create_mock_chat_response(content: str, model: str = "gpt-4", provider: str = "openai") -> ChatCompletionResponse:
    """Create a properly structured mock chat response for tests."""
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


class TestEssentialIntegration:
    """Essential integration tests for core workflows."""

    @pytest.fixture
    def service(self):
        """Create a basic LLM service for testing."""
        config = LLMCallerConfig(
            providers={
                "openai": ProviderConfig(
                    enabled=True,
                    api_key="test-key"
                )
            }
        )
        return LLMService(config)

    @pytest.mark.asyncio
    async def test_chat_completion_end_to_end(self, service):
        """Test: Chat completion works from request to response."""
        # Mock provider initialization
        with patch.object(service.provider_manager, 'initialize_providers'):
            await service.initialize()

            # Mock provider responses
            mock_response = create_mock_chat_response("Test response")

            with patch.object(service.provider_manager, 'get_available_providers',
                             return_value=["openai"]):
                with patch.object(service.provider_manager, 'get_provider') as mock_get_provider:
                    mock_provider = AsyncMock()
                    mock_provider.chat_completion.return_value = mock_response
                    mock_get_provider.return_value = mock_provider

                    # Execute workflow
                    messages = [{"role": "user", "content": "Test question"}]
                    response = await service.chat_completion(messages)

                    # Verify end-to-end success
                    assert response.provider == "openai"
                    assert response.choices[0].message.content == "Test response"
                    assert service._metrics["total_requests"] == 1
                    assert service._metrics["successful_requests"] == 1

            await service.cleanup()

    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self, service):
        """Test: Metrics are collected throughout the workflow."""
        with patch.object(service.provider_manager, 'initialize_providers'):
            await service.initialize()

            mock_response = create_mock_chat_response("Response")

            with patch.object(service.provider_manager, 'get_available_providers',
                             return_value=["openai"]):
                with patch.object(service.provider_manager, 'get_provider') as mock_get_provider:
                    mock_provider = AsyncMock()
                    mock_provider.chat_completion.return_value = mock_response
                    mock_get_provider.return_value = mock_provider

                    # Make multiple requests
                    for i in range(3):
                        messages = [{"role": "user", "content": f"Request {i}"}]
                        await service.chat_completion(messages, task_type=TaskType.GENERAL)

                    # Check metrics integration
                    metrics = await service.get_metrics()
                    assert metrics.total_requests == 3
                    assert metrics.successful_requests == 3
                    assert "openai" in metrics.provider_breakdown
                    assert "general" in metrics.task_breakdown

            await service.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, service):
        """Test: Error handling works throughout the workflow."""
        with patch.object(service.provider_manager, 'initialize_providers'):
            await service.initialize()

            # Mock no providers available
            with patch.object(service.provider_manager, 'get_available_providers',
                             return_value=[]):
                messages = [{"role": "user", "content": "Test"}]

                with pytest.raises(Exception) as exc_info:
                    await service.chat_completion(messages)

                # Verify error handling integration
                assert "No providers available" in str(exc_info.value)
                assert service._metrics["total_requests"] == 1
                assert service._metrics["failed_requests"] == 1

            await service.cleanup()


class TestConfigurationIntegration:
    """Integration tests for configuration workflows."""

    @pytest.mark.asyncio
    async def test_environment_config_integration(self):
        """Test: Environment variables are integrated into configuration."""
        test_env = {
            "OPENAI_API_KEY": "env-test-key",
            "LLM_CALLER_PORT": "9000"
        }

        with patch.dict(os.environ, test_env):
            from src.config.settings import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_config()

            # Verify environment integration
            assert config.providers["openai"].api_key == "env-test-key"
            assert config.port == 9000

            # Test service uses configuration
            service = LLMService(config)
            assert service.config.port == 9000
            assert service.config.providers["openai"].api_key == "env-test-key"

    @pytest.mark.asyncio
    async def test_config_validation_integration(self):
        """Test: Configuration validation works end-to-end."""
        from src.config.settings import ConfigManager

        # Create config with validation issues
        invalid_config_data = {
            "providers": {
                "openai": {
                    "enabled": True,
                    "api_key": None
                }
            }
        }

        with patch('llm_caller_cli.src.config.settings.yaml.safe_load', return_value=invalid_config_data):
            with patch('os.path.exists', return_value=True):
                config_manager = ConfigManager()
                is_valid, errors = config_manager.validate_config()

                # Verify validation integration
                assert not is_valid
                assert len(errors) > 0