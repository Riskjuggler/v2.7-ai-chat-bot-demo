"""
TDD Tests for configuration management.

These tests drive the configuration system design and ensure proper
environment handling, validation, and file management.
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, Mock
from llm_caller_cli.src.config.settings import (
    ConfigManager,
    LLMCallerConfig,
    ProviderConfig,
    RoutingConfig,
    LoggingConfig,
    get_config,
    reload_config,
    get_config_manager
)


class TestLLMCallerConfigModel:
    """Test the LLMCallerConfig pydantic model."""

    def test_config_model_defaults(self):
        """Test that config model has sensible defaults."""
        config = LLMCallerConfig()

        assert config.host == "localhost"
        assert config.port == 8080
        assert config.debug is False
        assert config.workers == 1
        assert isinstance(config.providers, dict)
        assert isinstance(config.routing, RoutingConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_config_model_custom_values(self):
        """Test that config model accepts custom values."""
        config = LLMCallerConfig(
            host="custom-host",
            port=9999,
            debug=True,
            workers=4
        )

        assert config.host == "custom-host"
        assert config.port == 9999
        assert config.debug is True
        assert config.workers == 4

    def test_config_model_provider_validation(self):
        """Test that provider configurations are validated."""
        provider_dict = {
            "openai": {
                "enabled": True,
                "api_key": "sk-test",
                "timeout": 30.0
            }
        }

        config = LLMCallerConfig(providers=provider_dict)

        assert isinstance(config.providers["openai"], ProviderConfig)
        assert config.providers["openai"].enabled is True
        assert config.providers["openai"].api_key == "sk-test"
        assert config.providers["openai"].timeout == 30.0

    def test_get_provider_config_existing(self):
        """Test getting configuration for existing provider."""
        config = LLMCallerConfig()
        config.providers["test"] = ProviderConfig(enabled=True, api_key="test-key")

        provider_config = config.get_provider_config("test")

        assert provider_config is not None
        assert provider_config.enabled is True
        assert provider_config.api_key == "test-key"

    def test_get_provider_config_missing(self):
        """Test getting configuration for missing provider."""
        config = LLMCallerConfig()

        provider_config = config.get_provider_config("nonexistent")
        assert provider_config is None

    def test_is_provider_enabled_true(self):
        """Test checking if provider is enabled when it is."""
        config = LLMCallerConfig()
        config.providers["test"] = ProviderConfig(enabled=True)

        assert config.is_provider_enabled("test") is True

    def test_is_provider_enabled_false(self):
        """Test checking if provider is enabled when it's not."""
        config = LLMCallerConfig()
        config.providers["test"] = ProviderConfig(enabled=False)

        assert config.is_provider_enabled("test") is False

    def test_is_provider_enabled_missing(self):
        """Test checking if provider is enabled when it doesn't exist."""
        config = LLMCallerConfig()

        assert config.is_provider_enabled("nonexistent") is False

    def test_get_enabled_providers(self):
        """Test getting list of enabled providers."""
        config = LLMCallerConfig()
        config.providers = {
            "enabled1": ProviderConfig(enabled=True),
            "enabled2": ProviderConfig(enabled=True),
            "disabled": ProviderConfig(enabled=False)
        }

        enabled = config.get_enabled_providers()

        assert len(enabled) == 2
        assert "enabled1" in enabled
        assert "enabled2" in enabled
        assert "disabled" not in enabled


class TestProviderConfigModel:
    """Test the ProviderConfig model."""

    def test_provider_config_defaults(self):
        """Test that ProviderConfig has sensible defaults."""
        config = ProviderConfig()

        assert config.enabled is True
        assert config.api_key is None
        assert config.base_url is None
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.rate_limit_requests_per_minute is None
        assert config.rate_limit_tokens_per_minute is None
        assert config.extra_headers == {}

    def test_provider_config_custom_values(self):
        """Test that ProviderConfig accepts custom values."""
        config = ProviderConfig(
            enabled=False,
            api_key="sk-test",
            base_url="https://api.example.com",
            timeout=60.0,
            max_retries=5,
            rate_limit_requests_per_minute=100,
            extra_headers={"Custom": "Header"}
        )

        assert config.enabled is False
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.rate_limit_requests_per_minute == 100
        assert config.extra_headers == {"Custom": "Header"}


class TestConfigManagerInitialization:
    """Test ConfigManager initialization and path handling."""

    def test_config_manager_default_path(self):
        """Test that ConfigManager uses default path when none provided."""
        manager = ConfigManager()

        # Should have a default path
        assert manager.config_path is not None
        assert manager.config_path.endswith(".yaml")

    def test_config_manager_custom_path(self):
        """Test that ConfigManager uses custom path when provided."""
        custom_path = "/custom/path/config.yaml"
        manager = ConfigManager(custom_path)

        assert manager.config_path == custom_path

    def test_config_manager_finds_existing_config(self):
        """Test that ConfigManager finds existing config file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Mock the possible paths to include our temp file
            with patch.object(ConfigManager, '_get_default_config_path', return_value=temp_path):
                manager = ConfigManager()
                assert manager.config_path == temp_path
        finally:
            os.unlink(temp_path)

    @patch.dict(os.environ, {}, clear=True)
    def test_config_manager_loads_environment_variables(self):
        """Test that ConfigManager loads environment variables."""
        # Set some test environment variables
        test_env = {
            'OPENAI_API_KEY': 'sk-test-openai',
            'ANTHROPIC_API_KEY': 'sk-ant-test',
            'LLM_CALLER_HOST': 'test-host',
            'LLM_CALLER_PORT': '9999'
        }

        with patch.dict(os.environ, test_env):
            manager = ConfigManager()
            # Environment loading happens in _load_environment_variables
            # which is called during initialization


class TestConfigManagerLoading:
    """Test configuration loading functionality."""

    def test_load_config_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            'host': 'yaml-host',
            'port': 7777,
            'debug': True,
            'providers': {
                'openai': {
                    'enabled': True,
                    'timeout': 45.0
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(config_data, temp_file)
            temp_path = temp_file.name

        try:
            manager = ConfigManager(temp_path)
            config = manager.load_config()

            assert config.host == 'yaml-host'
            assert config.port == 7777
            assert config.debug is True
            assert config.providers['openai'].enabled is True
            assert config.providers['openai'].timeout == 45.0
        finally:
            os.unlink(temp_path)

    def test_load_config_environment_overrides_yaml(self):
        """Test that environment variables override YAML configuration."""
        # Create YAML with one value
        config_data = {
            'host': 'yaml-host',
            'port': 7777
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(config_data, temp_file)
            temp_path = temp_file.name

        try:
            # Set environment variable to override
            with patch.dict(os.environ, {'LLM_CALLER_HOST': 'env-host'}):
                manager = ConfigManager(temp_path)
                config = manager.load_config()

                # Environment should override YAML
                assert config.host == 'env-host'
                assert config.port == 7777  # From YAML
        finally:
            os.unlink(temp_path)

    def test_load_config_missing_file_uses_defaults(self):
        """Test that missing config file uses defaults with environment overrides."""
        nonexistent_path = "/nonexistent/config.yaml"

        with patch.dict(os.environ, {'LLM_CALLER_HOST': 'env-host'}):
            manager = ConfigManager(nonexistent_path)
            config = manager.load_config()

            # Should use environment override
            assert config.host == 'env-host'
            # Should use defaults for other values
            assert config.port == 8080
            assert config.debug is False

    def test_apply_environment_overrides_openai(self):
        """Test that OpenAI environment variables are applied correctly."""
        config_data = {}

        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-openai',
            'OPENAI_BASE_URL': 'https://custom-openai.com'
        }):
            manager = ConfigManager()
            result = manager._apply_environment_overrides(config_data)

            assert 'providers' in result
            assert 'openai' in result['providers']
            assert result['providers']['openai']['api_key'] == 'sk-test-openai'
            assert result['providers']['openai']['base_url'] == 'https://custom-openai.com'
            assert result['providers']['openai']['enabled'] is True

    def test_apply_environment_overrides_anthropic(self):
        """Test that Anthropic environment variables are applied correctly."""
        config_data = {}

        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'sk-ant-test',
            'ANTHROPIC_BASE_URL': 'https://custom-anthropic.com'
        }):
            manager = ConfigManager()
            result = manager._apply_environment_overrides(config_data)

            assert result['providers']['anthropic']['api_key'] == 'sk-ant-test'
            assert result['providers']['anthropic']['base_url'] == 'https://custom-anthropic.com'
            assert result['providers']['anthropic']['enabled'] is True

    def test_apply_environment_overrides_lmstudio(self):
        """Test that LMStudio environment variables are applied correctly."""
        config_data = {}

        with patch.dict(os.environ, {
            'LMSTUDIO_BASE_URL': 'http://custom-lmstudio:5555/v1'
        }):
            manager = ConfigManager()
            result = manager._apply_environment_overrides(config_data)

            assert result['providers']['lmstudio']['base_url'] == 'http://custom-lmstudio:5555/v1'
            assert result['providers']['lmstudio']['enabled'] is True

    def test_apply_environment_overrides_service_config(self):
        """Test that service configuration environment variables are applied."""
        config_data = {}

        with patch.dict(os.environ, {
            'LLM_CALLER_HOST': 'custom-host',
            'LLM_CALLER_PORT': '9999',
            'LLM_CALLER_DEBUG': 'true',
            'LLM_CALLER_LOG_LEVEL': 'DEBUG'
        }):
            manager = ConfigManager()
            result = manager._apply_environment_overrides(config_data)

            assert result['host'] == 'custom-host'
            assert result['port'] == 9999
            assert result['debug'] is True
            assert result['logging']['level'] == 'DEBUG'

    def test_add_default_providers(self):
        """Test that default providers are added correctly."""
        config_data = {}

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test'}):
            manager = ConfigManager()
            result = manager._add_default_providers(config_data)

            # Should add all default providers
            assert 'providers' in result
            assert 'openai' in result['providers']
            assert 'anthropic' in result['providers']
            assert 'lmstudio' in result['providers']

            # OpenAI should be enabled due to API key
            assert result['providers']['openai']['enabled'] is True
            # Anthropic should be disabled (no API key)
            assert result['providers']['anthropic']['enabled'] is False
            # LMStudio should be enabled by default
            assert result['providers']['lmstudio']['enabled'] is True


class TestConfigManagerSaving:
    """Test configuration saving functionality."""

    def test_save_config_creates_directory(self):
        """Test that save_config creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "subdir", "config.yaml")
            config = LLMCallerConfig(host="test-host")

            manager = ConfigManager(config_path)
            manager.save_config(config)

            # Directory should be created
            assert os.path.exists(os.path.dirname(config_path))
            # File should be created
            assert os.path.exists(config_path)

    def test_save_config_sanitizes_api_keys(self):
        """Test that save_config removes sensitive API keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.yaml")

            config = LLMCallerConfig()
            config.providers["openai"] = ProviderConfig(
                enabled=True,
                api_key="sk-sensitive-key"
            )

            manager = ConfigManager(config_path)
            manager.save_config(config)

            # Read back the saved file
            with open(config_path, 'r') as f:
                saved_data = yaml.safe_load(f)

            # API key should be sanitized
            assert saved_data['providers']['openai']['api_key'] == '<set_via_environment>'

    def test_save_config_preserves_structure(self):
        """Test that save_config preserves configuration structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.yaml")

            config = LLMCallerConfig(
                host="test-host",
                port=9999,
                debug=True
            )

            manager = ConfigManager(config_path)
            manager.save_config(config)

            # Read back and verify structure
            with open(config_path, 'r') as f:
                saved_data = yaml.safe_load(f)

            assert saved_data['host'] == 'test-host'
            assert saved_data['port'] == 9999
            assert saved_data['debug'] is True


class TestConfigManagerValidation:
    """Test configuration validation functionality."""

    def test_validate_config_valid_configuration(self):
        """Test validation of valid configuration."""
        config = LLMCallerConfig()
        config.providers["openai"] = ProviderConfig(
            enabled=True,
            api_key="sk-test"
        )

        # Mock the get_config to return our test config
        with patch('llm_caller_cli.src.config.settings.ConfigManager.get_config', return_value=config):
            manager = ConfigManager()
            is_valid, errors = manager.validate_config()

            assert is_valid is True
            assert len(errors) == 0

    def test_validate_config_no_providers_enabled(self):
        """Test validation when no providers are enabled."""
        config = LLMCallerConfig()
        config.providers["openai"] = ProviderConfig(enabled=False)

        with patch('llm_caller_cli.src.config.settings.ConfigManager.get_config', return_value=config):
            manager = ConfigManager()
            is_valid, errors = manager.validate_config()

            assert is_valid is False
            assert "No providers are enabled" in errors

    def test_validate_config_missing_api_keys(self):
        """Test validation when required API keys are missing."""
        config = LLMCallerConfig()
        config.providers["openai"] = ProviderConfig(
            enabled=True,
            api_key=None  # Missing API key
        )

        with patch('llm_caller_cli.src.config.settings.ConfigManager.get_config', return_value=config):
            manager = ConfigManager()
            is_valid, errors = manager.validate_config()

            assert is_valid is False
            assert any("openai is enabled but no API key provided" in error for error in errors)

    def test_validate_config_invalid_default_provider(self):
        """Test validation when default provider is not enabled."""
        config = LLMCallerConfig()
        config.providers["openai"] = ProviderConfig(enabled=False)
        config.routing.default_provider = "openai"

        with patch('llm_caller_cli.src.config.settings.ConfigManager.get_config', return_value=config):
            manager = ConfigManager()
            is_valid, errors = manager.validate_config()

            assert is_valid is False
            assert any("Default provider 'openai' is not enabled" in error for error in errors)

    def test_validate_config_handles_exceptions(self):
        """Test validation handles exceptions gracefully."""
        with patch('llm_caller_cli.src.config.settings.ConfigManager.get_config', side_effect=Exception("Config error")):
            manager = ConfigManager()
            is_valid, errors = manager.validate_config()

            assert is_valid is False
            assert len(errors) == 1
            assert "Configuration validation failed: Config error" in errors[0]


class TestConfigManagerUtilities:
    """Test utility functions and global access."""

    def test_create_default_config(self):
        """Test creation of default configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.yaml")

            manager = ConfigManager(config_path)
            created_path = manager.create_default_config()

            assert created_path == config_path
            assert os.path.exists(config_path)

            # Should also create example .env file
            env_example_path = os.path.join(temp_dir, ".env.example")
            assert os.path.exists(env_example_path)

    def test_get_config_loads_and_caches(self):
        """Test that get_config loads and caches configuration."""
        manager = ConfigManager()

        with patch.object(manager, 'load_config') as mock_load:
            mock_config = LLMCallerConfig(host="test-host")
            mock_load.return_value = mock_config

            # First call should load
            config1 = manager.get_config()
            assert config1.host == "test-host"
            mock_load.assert_called_once()

            # Second call should use cache
            config2 = manager.get_config()
            assert config2 == config1
            mock_load.assert_called_once()  # Still only called once

    def test_reload_config_clears_cache(self):
        """Test that reload_config clears cache and reloads."""
        manager = ConfigManager()

        with patch.object(manager, 'load_config') as mock_load:
            mock_config1 = LLMCallerConfig(host="host1")
            mock_config2 = LLMCallerConfig(host="host2")
            mock_load.side_effect = [mock_config1, mock_config2]

            # Load initial config
            config1 = manager.get_config()
            assert config1.host == "host1"

            # Reload should clear cache and load again
            config2 = manager.reload_config()
            assert config2.host == "host2"
            assert mock_load.call_count == 2

    def test_global_config_manager_singleton(self):
        """Test that global config manager maintains singleton behavior."""
        from src.config.settings import get_config_manager

        # Reset global state
        import src.config.settings
        src.config.settings._config_manager = None

        # First call creates instance
        manager1 = get_config_manager()
        # Second call returns same instance
        manager2 = get_config_manager()

        assert manager1 is manager2

    def test_global_config_manager_with_custom_path(self):
        """Test that global config manager can use custom path."""
        from src.config.settings import get_config_manager

        # Reset global state
        import src.config.settings
        src.config.settings._config_manager = None

        custom_path = "/custom/path/config.yaml"
        manager = get_config_manager(custom_path)

        assert manager.config_path == custom_path

    def test_global_get_config_function(self):
        """Test global get_config convenience function."""
        with patch('llm_caller_cli.src.config.settings.get_config_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_config = LLMCallerConfig(host="test-host")
            mock_manager.get_config.return_value = mock_config
            mock_get_manager.return_value = mock_manager

            config = get_config()

            assert config.host == "test-host"
            mock_get_manager.assert_called_once()
            mock_manager.get_config.assert_called_once()

    def test_global_reload_config_function(self):
        """Test global reload_config convenience function."""
        with patch('llm_caller_cli.src.config.settings.get_config_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_config = LLMCallerConfig(host="reloaded-host")
            mock_manager.reload_config.return_value = mock_config
            mock_get_manager.return_value = mock_manager

            config = reload_config()

            assert config.host == "reloaded-host"
            mock_get_manager.assert_called_once()
            mock_manager.reload_config.assert_called_once()