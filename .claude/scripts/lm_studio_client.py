#!/usr/bin/env python3
"""
LM Studio Integration Wrapper

Provides REST API client for local LM Studio server with graceful
fallback to OpenAI API when LM Studio is unavailable.
"""

import os
import time
from typing import List, Optional, Dict
from pathlib import Path
import yaml

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Run: pip install requests")
    raise

# Import error handler for centralized retry logic
try:
    from error_handler import retry_on_transient_error
except ImportError:
    # Fallback if error_handler not available
    def retry_on_transient_error(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class LMStudioClient:
    """REST API client for LM Studio embedding generation"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize LM Studio client

        Args:
            config_path: Path to config YAML file (optional)
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'lm-studio-config.yaml'

        self.config = self._load_config(config_path)

        # Client settings
        self.base_url = self.config.get('lm_studio_url', 'http://localhost:1234')
        self.timeout = self.config.get('timeout_seconds', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.model_name = self.config.get('model_name', 'nomic-embed-text-v1.5')

        # OpenAI fallback
        self.openai_api_key = self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        self.use_fallback = False

    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from YAML file"""
        if not config_path.exists():
            # Return default config if file doesn't exist
            return {
                'lm_studio_url': 'http://localhost:1234',
                'timeout_seconds': 30,
                'max_retries': 3,
                'model_name': 'nomic-embed-text-v1.5'
            }

        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def check_health(self) -> bool:
        """
        Check if LM Studio server is running and accessible

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            # Try v1/models endpoint (more reliable than /health)
            response = requests.get(
                f'{self.base_url}/v1/models',
                timeout=2  # Fast timeout for health check
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_loaded_models(self) -> List[str]:
        """
        Get list of loaded models from LM Studio

        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f'{self.base_url}/v1/models',
                timeout=self.timeout
            )

            if response.status_code != 200:
                return []

            data = response.json()
            # OpenAI-compatible format: {"data": [{"id": "model-name"}, ...]}
            if 'data' in data:
                return [model['id'] for model in data['data']]
            return []

        except requests.exceptions.RequestException:
            return []

    def validate_model_loaded(self) -> bool:
        """
        Validate that expected model is loaded

        Returns:
            True if model is loaded, False otherwise
        """
        loaded_models = self.get_loaded_models()
        return self.model_name in loaded_models

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text

        Args:
            text: Input text to embed

        Returns:
            1536-dim embedding vector, or None if failed
        """
        # Check if we should use OpenAI fallback
        if self.use_fallback and self.openai_api_key:
            return self._generate_embedding_openai(text)

        # Try LM Studio with retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    f'{self.base_url}/v1/embeddings',
                    json={
                        'model': self.model_name,
                        'input': text
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    # OpenAI-compatible format: {"data": [{"embedding": [...]}]}
                    if 'data' in result and len(result['data']) > 0:
                        return result['data'][0]['embedding']
                    else:
                        raise ValueError(f"Unexpected response format: {result}")

                # Non-200 status - log and retry
                print(f"LM Studio error (attempt {attempt}/{self.max_retries}): "
                      f"HTTP {response.status_code} - {response.text[:100]}")

                if attempt < self.max_retries:
                    # Exponential backoff: 10s, 30s, 90s
                    backoff = 10 * (3 ** (attempt - 1))
                    time.sleep(backoff)
                else:
                    # Final attempt failed - try fallback
                    if self.openai_api_key:
                        print("LM Studio unavailable - falling back to OpenAI API")
                        self.use_fallback = True
                        return self._generate_embedding_openai(text)
                    return None

            except requests.exceptions.Timeout:
                print(f"LM Studio timeout (attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    backoff = 10 * (3 ** (attempt - 1))
                    time.sleep(backoff)
                else:
                    # Final attempt failed - try fallback
                    if self.openai_api_key:
                        print("LM Studio unavailable - falling back to OpenAI API")
                        self.use_fallback = True
                        return self._generate_embedding_openai(text)
                    return None

            except requests.exceptions.RequestException as e:
                print(f"LM Studio connection error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    backoff = 10 * (3 ** (attempt - 1))
                    time.sleep(backoff)
                else:
                    # Final attempt failed - try fallback
                    if self.openai_api_key:
                        print("LM Studio unavailable - falling back to OpenAI API")
                        self.use_fallback = True
                        return self._generate_embedding_openai(text)
                    return None

        return None

    def _generate_embedding_openai(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using OpenAI API as fallback

        Args:
            text: Input text to embed

        Returns:
            Embedding vector, or None if failed
        """
        try:
            response = requests.post(
                'https://api.openai.com/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'text-embedding-3-small',  # 1536 dims, compatible
                    'input': text
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                if 'data' in result and len(result['data']) > 0:
                    return result['data'][0]['embedding']

            print(f"OpenAI API error: HTTP {response.status_code}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"OpenAI API connection error: {e}")
            return None


def main():
    """CLI entry point for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 lm_studio_client.py <command> [args]")
        print("")
        print("Commands:")
        print("  health              - Check LM Studio health")
        print("  models              - List loaded models")
        print("  validate            - Validate expected model loaded")
        print("  embed <text>        - Generate embedding for text")
        return 1

    client = LMStudioClient()
    command = sys.argv[1]

    if command == 'health':
        healthy = client.check_health()
        print(f"LM Studio health: {'OK' if healthy else 'UNAVAILABLE'}")
        return 0 if healthy else 1

    elif command == 'models':
        models = client.get_loaded_models()
        print(f"Loaded models ({len(models)}):")
        for model in models:
            print(f"  - {model}")
        return 0

    elif command == 'validate':
        valid = client.validate_model_loaded()
        if valid:
            print(f"Model '{client.model_name}' is loaded")
            return 0
        else:
            print(f"ERROR: Model '{client.model_name}' not loaded")
            print(f"Loaded models: {client.get_loaded_models()}")
            return 1

    elif command == 'embed':
        if len(sys.argv) < 3:
            print("ERROR: Missing text argument")
            return 1

        text = sys.argv[2]
        embedding = client.generate_embedding(text)

        if embedding:
            print(f"Embedding generated: {len(embedding)} dimensions")
            print(f"First 5 values: {embedding[:5]}")
            return 0
        else:
            print("ERROR: Failed to generate embedding")
            return 1

    else:
        print(f"ERROR: Unknown command '{command}'")
        return 1


if __name__ == '__main__':
    exit(main())
