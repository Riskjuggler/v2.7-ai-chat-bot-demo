"""Service layer for LLM integration."""

import sys
from pathlib import Path
from datetime import datetime

# Add llm_caller_cli to path
project_root = Path(__file__).parent.parent.parent
llm_module_path = project_root / "llm_caller_cli"
if str(llm_module_path) not in sys.path:
    sys.path.insert(0, str(llm_module_path))

# Import from llm_caller_cli
from llm_caller_cli import LLMService as LLMCaller, ChatCompletionRequest


class LLMService:
    """Service for calling LLM via llm_caller_cli."""

    def __init__(self):
        """Initialize LLM service with default settings."""
        self.llm_service = LLMCaller()
        self.provider = "lmstudio"

    async def chat(self, message: str) -> tuple[str, str, datetime]:
        """
        Send a message to the LLM and get response.

        Args:
            message: User message to send to LLM

        Returns:
            Tuple of (response_text, model_name, timestamp)

        Raises:
            TimeoutError: If LLM request times out
            ConnectionError: If cannot connect to LLM service
            ValueError: If LLM returns invalid response
        """
        try:
            # Create chat request
            request = ChatCompletionRequest(
                messages=[{"role": "user", "content": message}],
                provider=self.provider,
                max_tokens=1000,
            )

            # Call LLM service
            response = await self.llm_service.chat_completion(request)

            # Extract response data
            response_text = response.content
            model_name = response.model or self.provider

            return response_text, model_name, datetime.now()

        except TimeoutError as e:
            raise TimeoutError(f"LLM request timeout: {e}") from e
        except ConnectionError as e:
            raise ConnectionError(f"Cannot connect to LLM service: {e}") from e
        except Exception as e:
            raise ValueError(f"LLM error: {e}") from e

    async def health_check(self) -> bool:
        """
        Check if LLM service is available.

        Returns:
            True if LLM service is reachable, False otherwise
        """
        try:
            # Simple health check - try to call LLM with minimal message
            await self.chat("test")
            return True
        except Exception:
            return False
