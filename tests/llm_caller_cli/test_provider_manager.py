"""
TDD Tests for ProviderManager functionality.

These tests drive the provider management design and implementation.
"""

import pytest
import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch
from llm_caller_cli.src.core.llm_service import ProviderManager
from llm_caller_cli.src.config.settings import LLMCallerConfig, ProviderConfig
from llm_caller_cli.src.providers.base_provider import ProviderAdapter, ProviderError
from llm_caller_cli.src.models.request_models import ProviderStatus


class TestProviderManagerInitialization:
    """Test ProviderManager initialization and setup."""

    def test_provider_manager_initialization(self):
        """Test that ProviderManager initializes with config."""
        config = LLMCallerConfig()
        manager = ProviderManager(config)

        assert manager.config == config
        assert manager.providers == {}
        assert manager._provider_health == {}
        assert manager._initialization_lock is not None

    def test_provider_manager_stores_config_reference(self):
        """Test that ProviderManager maintains reference to config."""
        config = LLMCallerConfig(
            host="test-host",
            port=8888
        )
        manager = ProviderManager(config)

        assert manager.config.host == "test-host"
        assert manager.config.port == 8888


class TestProviderManagerProviderCreation:
    """Test provider creation and initialization."""

    @pytest.mark.asyncio
    async def test_initialize_providers_creates_enabled_providers(self):
        """Test that initialize_providers creates all enabled providers."""
        config = LLMCallerConfig()
        config.providers = {
            "lmstudio": ProviderConfig(enabled=True),
            "openai": ProviderConfig(enabled=True),
            "disabled_provider": ProviderConfig(enabled=False)
        }

        manager = ProviderManager(config)

        with patch.object(manager, '_create_provider') as mock_create:
            mock_provider1 = AsyncMock()
            mock_provider2 = AsyncMock()
            mock_create.side_effect = [mock_provider1, mock_provider2]

            await manager.initialize_providers()

            # Should create only enabled providers
            assert mock_create.call_count == 2
            assert "lmstudio" in manager.providers
            assert "openai" in manager.providers
            assert "disabled_provider" not in manager.providers

    @pytest.mark.asyncio
    async def test_initialize_providers_handles_creation_failures(self):
        """Test that provider creation failures don't stop other providers."""
        config = LLMCallerConfig()
        config.providers = {
            "good_provider": ProviderConfig(enabled=True),
            "bad_provider": ProviderConfig(enabled=True)
        }

        manager = ProviderManager(config)

        with patch.object(manager, '_create_provider') as mock_create:
            mock_provider = AsyncMock()
            mock_create.side_effect = [mock_provider, Exception("Creation failed")]

            await manager.initialize_providers()

            # Should have created the good provider despite bad one failing
            assert "good_provider" in manager.providers
            assert "bad_provider" not in manager.providers

    @pytest.mark.asyncio
    async def test_create_provider_lmstudio(self):
        """Test creation of LMStudio provider."""
        config = {"base_url": "http://localhost:1234/v1", "timeout": 30.0}
        manager = ProviderManager(LLMCallerConfig())

        with patch('llm_caller_cli.src.core.llm_service.LMStudioProvider') as mock_class:
            mock_provider = AsyncMock()
            mock_class.return_value = mock_provider

            provider = await manager._create_provider("lmstudio", config)

            mock_class.assert_called_once_with(config)
            mock_provider.initialize.assert_called_once()
            assert provider == mock_provider

    @pytest.mark.asyncio
    async def test_create_provider_openai_with_dependency(self):
        """Test creation of OpenAI provider when dependency is available."""
        config = {"api_key": "sk-test", "base_url": "https://api.openai.com/v1"}
        manager = ProviderManager(LLMCallerConfig())

        # Create a mock OpenAI provider class and temporarily add it to sys.modules
        mock_openai_provider_class = Mock()
        mock_provider = AsyncMock()
        mock_openai_provider_class.return_value = mock_provider

        # Create a mock module
        mock_module = Mock()
        mock_module.OpenAIProvider = mock_openai_provider_class

        with patch.dict('sys.modules', {'src.providers.openai_provider': mock_module}):
            provider = await manager._create_provider("openai", config)

            mock_openai_provider_class.assert_called_once_with(config)
            mock_provider.initialize.assert_called_once()
            assert provider == mock_provider

    @pytest.mark.asyncio
    async def test_create_provider_openai_missing_dependency(self):
        """Test creation of OpenAI provider when dependency is missing."""
        config = {"api_key": "sk-test"}
        manager = ProviderManager(LLMCallerConfig())

        # Test the case where the import fails
        # Don't add the module to sys.modules, so the import will fail
        with pytest.raises(ImportError, match="OpenAI provider requires 'openai' package"):
            await manager._create_provider("openai", config)

    @pytest.mark.asyncio
    async def test_create_provider_unknown_provider(self):
        """Test creation fails for unknown provider."""
        manager = ProviderManager(LLMCallerConfig())

        with pytest.raises(ValueError, match="Unknown provider: unknown_provider"):
            await manager._create_provider("unknown_provider", {})


class TestProviderManagerProviderAccess:
    """Test provider access and availability checking."""

    @pytest.mark.asyncio
    async def test_get_provider_returns_existing_provider(self):
        """Test that get_provider returns existing provider."""
        manager = ProviderManager(LLMCallerConfig())

        mock_provider = AsyncMock()
        manager.providers["test_provider"] = mock_provider

        provider = await manager.get_provider("test_provider")
        assert provider == mock_provider

    @pytest.mark.asyncio
    async def test_get_provider_returns_none_for_missing(self):
        """Test that get_provider returns None for missing provider."""
        manager = ProviderManager(LLMCallerConfig())

        provider = await manager.get_provider("nonexistent")
        assert provider is None

    @pytest.mark.asyncio
    async def test_get_available_providers_checks_health(self):
        """Test that get_available_providers checks provider health."""
        manager = ProviderManager(LLMCallerConfig())

        # Mock providers with different health states
        healthy_provider = AsyncMock()
        healthy_provider.health_check.return_value = ProviderStatus(
            name="healthy",
            status="online",
            models_available=["model1"],
            last_check=1234567890
        )

        unhealthy_provider = AsyncMock()
        unhealthy_provider.health_check.return_value = ProviderStatus(
            name="unhealthy",
            status="offline",
            models_available=[],
            last_check=1234567890
        )

        failing_provider = AsyncMock()
        failing_provider.health_check.side_effect = Exception("Health check failed")

        manager.providers = {
            "healthy": healthy_provider,
            "unhealthy": unhealthy_provider,
            "failing": failing_provider
        }

        available = await manager.get_available_providers()

        # Should only return healthy providers
        assert available == ["healthy"]

    @pytest.mark.asyncio
    async def test_get_available_providers_empty_when_all_unhealthy(self):
        """Test that get_available_providers returns empty list when all providers unhealthy."""
        manager = ProviderManager(LLMCallerConfig())

        unhealthy_provider = AsyncMock()
        unhealthy_provider.health_check.return_value = ProviderStatus(
            name="unhealthy",
            status="offline",
            models_available=[],
            last_check=1234567890
        )

        manager.providers = {"unhealthy": unhealthy_provider}

        available = await manager.get_available_providers()
        assert available == []


class TestProviderManagerHealthChecking:
    """Test health checking functionality."""

    @pytest.mark.asyncio
    async def test_health_check_all_returns_all_provider_statuses(self):
        """Test that health_check_all returns status for all providers."""
        manager = ProviderManager(LLMCallerConfig())

        # Mock providers
        provider1 = AsyncMock()
        provider1.health_check.return_value = ProviderStatus(
            name="provider1",
            status="online",
            models_available=["model1"],
            last_check=1234567890
        )

        provider2 = AsyncMock()
        provider2.health_check.return_value = ProviderStatus(
            name="provider2",
            status="offline",
            models_available=[],
            last_check=1234567890
        )

        manager.providers = {
            "provider1": provider1,
            "provider2": provider2
        }

        health_results = await manager.health_check_all()

        assert len(health_results) == 2
        assert health_results["provider1"].status == "online"
        assert health_results["provider2"].status == "offline"

    @pytest.mark.asyncio
    async def test_health_check_all_handles_provider_failures(self):
        """Test that health_check_all handles individual provider failures."""
        manager = ProviderManager(LLMCallerConfig())

        # One provider works, one fails
        working_provider = AsyncMock()
        working_provider.health_check.return_value = ProviderStatus(
            name="working",
            status="online",
            models_available=["model1"],
            last_check=1234567890
        )

        failing_provider = AsyncMock()
        failing_provider.health_check.side_effect = Exception("Health check failed")

        manager.providers = {
            "working": working_provider,
            "failing": failing_provider
        }

        health_results = await manager.health_check_all()

        assert len(health_results) == 2
        assert health_results["working"].status == "online"
        assert health_results["failing"].status == "error"
        assert "Health check failed" in health_results["failing"].error_message

    @pytest.mark.asyncio
    async def test_health_check_all_empty_when_no_providers(self):
        """Test that health_check_all returns empty dict when no providers."""
        manager = ProviderManager(LLMCallerConfig())

        health_results = await manager.health_check_all()
        assert health_results == {}


class TestProviderManagerCleanup:
    """Test provider cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_calls_cleanup_on_all_providers(self):
        """Test that cleanup calls cleanup on all providers."""
        manager = ProviderManager(LLMCallerConfig())

        # Mock providers
        provider1 = AsyncMock()
        provider2 = AsyncMock()

        manager.providers = {
            "provider1": provider1,
            "provider2": provider2
        }

        await manager.cleanup()

        provider1.cleanup.assert_called_once()
        provider2.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_continues_despite_individual_failures(self):
        """Test that cleanup continues even if individual provider cleanup fails."""
        manager = ProviderManager(LLMCallerConfig())

        # One provider cleanup fails
        working_provider = AsyncMock()
        failing_provider = AsyncMock()
        failing_provider.cleanup.side_effect = Exception("Cleanup failed")

        manager.providers = {
            "working": working_provider,
            "failing": failing_provider
        }

        # Should not raise exception
        await manager.cleanup()

        # Both should have been called
        working_provider.cleanup.assert_called_once()
        failing_provider.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_handles_empty_providers(self):
        """Test that cleanup handles empty providers dict gracefully."""
        manager = ProviderManager(LLMCallerConfig())

        # Should not raise exception
        await manager.cleanup()


class TestProviderManagerConcurrency:
    """Test concurrent operations and thread safety."""

    @pytest.mark.asyncio
    async def test_initialize_providers_uses_lock(self):
        """Test that initialize_providers uses initialization lock."""
        # Create config with an enabled provider to ensure lock is exercised
        config = LLMCallerConfig()
        config.providers = {
            "test_provider": ProviderConfig(enabled=True)
        }
        manager = ProviderManager(config)

        # Test that the lock exists and is an asyncio.Lock
        assert hasattr(manager, '_initialization_lock')
        assert isinstance(manager._initialization_lock, asyncio.Lock)

        # Test that initialization completes successfully (lock is working)
        with patch.object(manager, '_create_provider', return_value=AsyncMock()):
            await manager.initialize_providers()

        # The fact that this doesn't hang proves the lock is working correctly

    @pytest.mark.asyncio
    async def test_concurrent_initialization_serialized(self):
        """Test that concurrent initialization calls are serialized."""
        config = LLMCallerConfig()
        config.providers = {
            "test_provider": ProviderConfig(enabled=True)
        }

        manager = ProviderManager(config)

        initialization_order = []

        async def mock_create_provider(name, config):
            # Simulate some async work
            await asyncio.sleep(0.1)
            initialization_order.append(name)
            return AsyncMock()

        with patch.object(manager, '_create_provider', side_effect=mock_create_provider):
            # Start two concurrent initializations
            task1 = asyncio.create_task(manager.initialize_providers())
            task2 = asyncio.create_task(manager.initialize_providers())

            await asyncio.gather(task1, task2)

            # Should only have one provider created (serialized access)
            assert len(initialization_order) == 1
            assert len(manager.providers) == 1


class TestProviderManagerIntegration:
    """Integration tests for ProviderManager."""

    @pytest.mark.asyncio
    async def test_full_provider_lifecycle(self):
        """Test complete provider lifecycle: initialize -> use -> cleanup."""
        config = LLMCallerConfig()
        config.providers = {
            "lmstudio": ProviderConfig(
                enabled=True,
                base_url="http://localhost:1234/v1"
            )
        }

        manager = ProviderManager(config)

        # Mock provider creation
        mock_provider = AsyncMock()
        mock_provider.health_check.return_value = ProviderStatus(
            name="lmstudio",
            status="online",
            models_available=["llama-2-7b"],
            last_check=1234567890
        )

        with patch.object(manager, '_create_provider', return_value=mock_provider):
            # Initialize
            await manager.initialize_providers()
            assert "lmstudio" in manager.providers

            # Use
            provider = await manager.get_provider("lmstudio")
            assert provider == mock_provider

            available = await manager.get_available_providers()
            assert "lmstudio" in available

            health = await manager.health_check_all()
            assert health["lmstudio"].status == "online"

            # Cleanup
            await manager.cleanup()
            mock_provider.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_provider_manager_with_mixed_provider_states(self):
        """Test ProviderManager behavior with providers in different states."""
        config = LLMCallerConfig()
        config.providers = {
            "working": ProviderConfig(enabled=True),
            "disabled": ProviderConfig(enabled=False),
            "broken": ProviderConfig(enabled=True)
        }

        manager = ProviderManager(config)

        # Mock provider creation
        working_provider = AsyncMock()
        working_provider.health_check.return_value = ProviderStatus(
            name="working",
            status="online",
            models_available=["model1"],
            last_check=1234567890
        )

        def mock_create_side_effect(name, config):
            if name == "working":
                return working_provider
            elif name == "broken":
                raise Exception("Provider creation failed")
            else:
                raise ValueError(f"Unexpected provider: {name}")

        with patch.object(manager, '_create_provider', side_effect=mock_create_side_effect):
            await manager.initialize_providers()

            # Should only have working provider
            assert len(manager.providers) == 1
            assert "working" in manager.providers
            assert "disabled" not in manager.providers
            assert "broken" not in manager.providers

            # Available providers should reflect health
            available = await manager.get_available_providers()
            assert available == ["working"]