"""Configuration management for LLM Caller service."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


class ProviderConfig(BaseModel):
    """Configuration for a specific provider."""
    enabled: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_tokens_per_minute: Optional[int] = None
    extra_headers: Dict[str, str] = Field(default_factory=dict)


class RoutingConfig(BaseModel):
    """Configuration for model routing."""
    enabled: bool = True
    default_provider: Optional[str] = None
    prefer_local: bool = False
    fallback_enabled: bool = True
    cost_optimization: bool = False
    max_cost_per_request: Optional[float] = None
    quality_threshold: float = 0.7
    speed_threshold: float = 0.5


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5
    log_requests: bool = True
    log_responses: bool = False  # May contain sensitive data
    log_errors: bool = True


class MetricsConfig(BaseModel):
    """Configuration for metrics collection."""
    enabled: bool = True
    prometheus_port: int = 9090
    collect_detailed_metrics: bool = True
    metrics_retention_days: int = 30


class SecurityConfig(BaseModel):
    """Configuration for security settings."""
    api_key_header: str = "X-API-Key"
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    rate_limiting: bool = True
    max_requests_per_minute: int = 100
    require_authentication: bool = False


class LLMCallerConfig(BaseModel):
    """Main configuration for LLM Caller service."""

    # Provider configurations
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)

    # Routing configuration
    routing: RoutingConfig = Field(default_factory=RoutingConfig)

    # Logging configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Metrics configuration
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)

    # Security configuration
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # Service configuration
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    workers: int = 1

    @field_validator('providers', mode='before')
    @classmethod
    def validate_providers(cls, v):
        """Validate provider configurations."""
        if isinstance(v, dict):
            return {name: ProviderConfig(**config) if isinstance(config, dict) else config
                   for name, config in v.items()}
        return v

    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider."""
        return self.providers.get(provider_name)

    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled."""
        provider_config = self.get_provider_config(provider_name)
        return provider_config.enabled if provider_config else False

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names."""
        return [
            name for name, config in self.providers.items()
            if config.enabled
        ]


class ConfigManager:
    """Configuration manager for LLM Caller service."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[LLMCallerConfig] = None
        self._load_environment_variables()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Try multiple locations
        possible_paths = [
            os.path.expanduser("~/.llm_caller/config.yaml"),
            os.path.join(os.getcwd(), "config.yaml"),
            os.path.join(os.path.dirname(__file__), "../../config.yaml")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Return the preferred location
        return os.path.expanduser("~/.llm_caller/config.yaml")

    def _load_environment_variables(self):
        """Load environment variables from .env file."""
        # Try to load from multiple locations
        possible_env_files = [
            os.path.expanduser("~/.llm_caller/.env"),
            os.path.join(os.getcwd(), ".env"),
            os.path.join(os.path.dirname(__file__), "../../.env")
        ]

        for env_file in possible_env_files:
            if os.path.exists(env_file):
                load_dotenv(env_file)
                break

    def load_config(self) -> LLMCallerConfig:
        """Load configuration from file and environment variables.

        Returns:
            Loaded configuration
        """
        config_data = {}

        # Load from YAML file if it exists
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}

        # Override with environment variables
        config_data = self._apply_environment_overrides(config_data)

        # Add default provider configurations
        config_data = self._add_default_providers(config_data)

        self._config = LLMCallerConfig(**config_data)
        return self._config

    def _apply_environment_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration.

        Args:
            config_data: Base configuration data

        Returns:
            Configuration with environment overrides applied
        """
        # Ensure providers section exists
        if 'providers' not in config_data:
            config_data['providers'] = {}

        # OpenAI configuration
        if os.getenv('OPENAI_API_KEY'):
            if 'openai' not in config_data['providers']:
                config_data['providers']['openai'] = {}
            config_data['providers']['openai']['api_key'] = os.getenv('OPENAI_API_KEY')
            config_data['providers']['openai']['enabled'] = True

        if os.getenv('OPENAI_BASE_URL'):
            if 'openai' not in config_data['providers']:
                config_data['providers']['openai'] = {}
            config_data['providers']['openai']['base_url'] = os.getenv('OPENAI_BASE_URL')

        # Anthropic configuration
        if os.getenv('ANTHROPIC_API_KEY'):
            if 'anthropic' not in config_data['providers']:
                config_data['providers']['anthropic'] = {}
            config_data['providers']['anthropic']['api_key'] = os.getenv('ANTHROPIC_API_KEY')
            config_data['providers']['anthropic']['enabled'] = True

        if os.getenv('ANTHROPIC_BASE_URL'):
            if 'anthropic' not in config_data['providers']:
                config_data['providers']['anthropic'] = {}
            config_data['providers']['anthropic']['base_url'] = os.getenv('ANTHROPIC_BASE_URL')

        # LMStudio configuration
        lmstudio_url = os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')
        if 'lmstudio' not in config_data['providers']:
            config_data['providers']['lmstudio'] = {}
        config_data['providers']['lmstudio']['base_url'] = lmstudio_url
        config_data['providers']['lmstudio']['enabled'] = True

        # Service configuration
        if os.getenv('LLM_CALLER_HOST'):
            config_data['host'] = os.getenv('LLM_CALLER_HOST')

        if os.getenv('LLM_CALLER_PORT'):
            config_data['port'] = int(os.getenv('LLM_CALLER_PORT'))

        if os.getenv('LLM_CALLER_DEBUG'):
            config_data['debug'] = os.getenv('LLM_CALLER_DEBUG').lower() == 'true'

        # Logging configuration
        if os.getenv('LLM_CALLER_LOG_LEVEL'):
            if 'logging' not in config_data:
                config_data['logging'] = {}
            config_data['logging']['level'] = os.getenv('LLM_CALLER_LOG_LEVEL')

        # Routing configuration
        if os.getenv('LLM_CALLER_PREFER_LOCAL'):
            if 'routing' not in config_data:
                config_data['routing'] = {}
            config_data['routing']['prefer_local'] = os.getenv('LLM_CALLER_PREFER_LOCAL').lower() == 'true'

        if os.getenv('LLM_CALLER_DEFAULT_PROVIDER'):
            if 'routing' not in config_data:
                config_data['routing'] = {}
            config_data['routing']['default_provider'] = os.getenv('LLM_CALLER_DEFAULT_PROVIDER')

        return config_data

    def _add_default_providers(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add default provider configurations.

        Args:
            config_data: Configuration data

        Returns:
            Configuration with default providers added
        """
        if 'providers' not in config_data:
            config_data['providers'] = {}

        # Default OpenAI configuration
        if 'openai' not in config_data['providers']:
            config_data['providers']['openai'] = {
                'enabled': bool(os.getenv('OPENAI_API_KEY')),
                'base_url': 'https://api.openai.com/v1',
                'timeout': 30.0,
                'max_retries': 3
            }

        # Default Anthropic configuration
        if 'anthropic' not in config_data['providers']:
            config_data['providers']['anthropic'] = {
                'enabled': bool(os.getenv('ANTHROPIC_API_KEY')),
                'base_url': 'https://api.anthropic.com',
                'timeout': 30.0,
                'max_retries': 3
            }

        # Default LMStudio configuration
        if 'lmstudio' not in config_data['providers']:
            config_data['providers']['lmstudio'] = {
                'enabled': True,
                'base_url': 'http://localhost:1234/v1',
                'timeout': 30.0,
                'max_retries': 2
            }

        return config_data

    def save_config(self, config: LLMCallerConfig):
        """Save configuration to file.

        Args:
            config: Configuration to save
        """
        # Create directory if it doesn't exist
        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        # Convert to dictionary and save
        config_dict = config.model_dump()

        # Remove sensitive information before saving
        for provider_name, provider_config in config_dict.get('providers', {}).items():
            if 'api_key' in provider_config:
                provider_config['api_key'] = '<set_via_environment>'

        with open(self.config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

    def get_config(self) -> LLMCallerConfig:
        """Get current configuration, loading if necessary.

        Returns:
            Current configuration
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def reload_config(self) -> LLMCallerConfig:
        """Reload configuration from file.

        Returns:
            Reloaded configuration
        """
        self._config = None
        return self.load_config()

    def create_default_config(self) -> str:
        """Create a default configuration file.

        Returns:
            Path to created configuration file
        """
        default_config = LLMCallerConfig()

        # Create directory
        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        # Save default configuration
        self.save_config(default_config)

        # Create example .env file
        env_path = os.path.join(config_dir, '.env.example')
        with open(env_path, 'w') as f:
            f.write("""# LLM Caller Environment Variables

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
# OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
# ANTHROPIC_BASE_URL=https://api.anthropic.com

# LMStudio Configuration
LMSTUDIO_BASE_URL=http://localhost:1234/v1

# Service Configuration
LLM_CALLER_HOST=localhost
LLM_CALLER_PORT=8080
LLM_CALLER_DEBUG=false
LLM_CALLER_LOG_LEVEL=INFO

# Routing Configuration
LLM_CALLER_PREFER_LOCAL=false
LLM_CALLER_DEFAULT_PROVIDER=openai
""")

        return self.config_path

    def validate_config(self) -> tuple[bool, List[str]]:
        """Validate current configuration.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            config = self.get_config()
            errors = []

            # Check if at least one provider is enabled
            enabled_providers = config.get_enabled_providers()
            if not enabled_providers:
                errors.append("No providers are enabled")

            # Validate provider-specific settings
            for provider_name, provider_config in config.providers.items():
                if provider_config.enabled:
                    if provider_name in ['openai', 'anthropic'] and not provider_config.api_key:
                        errors.append(f"{provider_name} is enabled but no API key provided")

            # Validate routing config
            if config.routing.default_provider and config.routing.default_provider not in enabled_providers:
                errors.append(f"Default provider '{config.routing.default_provider}' is not enabled")

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Configuration validation failed: {str(e)}"]


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Get global configuration manager instance.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Configuration manager instance
    """
    global _config_manager
    if _config_manager is None or config_path:
        _config_manager = ConfigManager(config_path)
    return _config_manager


def get_config() -> LLMCallerConfig:
    """Get current configuration.

    Returns:
        Current configuration
    """
    return get_config_manager().get_config()


def reload_config() -> LLMCallerConfig:
    """Reload configuration from file.

    Returns:
        Reloaded configuration
    """
    return get_config_manager().reload_config()