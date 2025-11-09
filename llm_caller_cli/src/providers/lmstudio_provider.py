"""LMStudio provider adapter for local model hosting."""

import json
import time
import uuid
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any
import aiohttp
from ..models.request_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderStatus,
    StreamChunk,
    Choice,
    Usage,
    ChatMessage,
    EmbeddingData
)
from .base_provider import (
    ProviderAdapter,
    ProviderError,
    ProviderTimeoutError,
    ProviderConnectionError,
    ProviderModelNotFoundError,
    ProviderInvalidRequestError
)


class LMStudioProvider(ProviderAdapter):
    """LMStudio provider for local model hosting with OpenAI-compatible API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize LMStudio provider.

        Args:
            config: Provider configuration containing base_url, timeout, etc.
        """
        super().__init__("lmstudio", config)
        self.base_url = config.get("base_url", "http://localhost:1234/v1")
        self.timeout = config.get("timeout", 30.0)
        self.max_retries = config.get("max_retries", 3)
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize HTTP session."""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            keepalive_timeout=30
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )

    async def cleanup(self):
        """Cleanup HTTP session."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        stream: bool = False
    ) -> Any:
        """Make HTTP request to LMStudio.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            stream: Whether to stream response

        Returns:
            Response data

        Raises:
            ProviderError: If request fails
        """
        if not self.session:
            await self.initialize()

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            async with self.session.request(
                method,
                url,
                json=data,
                headers={"Accept": "text/event-stream" if stream else "application/json"}
            ) as response:
                if response.status == 404:
                    raise ProviderModelNotFoundError(
                        f"Model or endpoint not found: {endpoint}",
                        self.name
                    )
                elif response.status == 400:
                    error_text = await response.text()
                    raise ProviderInvalidRequestError(
                        f"Invalid request: {error_text}",
                        self.name
                    )
                elif response.status >= 500:
                    error_text = await response.text()
                    raise ProviderError(
                        f"Server error: {error_text}",
                        self.name
                    )
                elif response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(
                        f"Request failed with status {response.status}: {error_text}",
                        self.name
                    )

                if stream:
                    return response
                else:
                    return await response.json()

        except (asyncio.TimeoutError, aiohttp.ServerTimeoutError):
            raise ProviderTimeoutError(
                f"Request to {url} timed out after {self.timeout}s",
                self.name
            )
        except aiohttp.ClientConnectionError as e:
            raise ProviderConnectionError(
                f"Failed to connect to LMStudio at {url}: {str(e)}",
                self.name
            )
        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(
                f"Unexpected error: {str(e)}",
                self.name
            )

    async def chat_completion(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Generate chat completion using LMStudio.

        Args:
            request: Chat completion request

        Returns:
            Chat completion response
        """
        # Convert to OpenAI-compatible format
        data = {
            "messages": [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ],
            "stream": False
        }

        # Add optional parameters
        if request.model:
            data["model"] = request.model
        if request.max_tokens:
            data["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            data["temperature"] = request.temperature
        if request.top_p is not None:
            data["top_p"] = request.top_p
        if request.stop:
            data["stop"] = request.stop
        if request.presence_penalty is not None:
            data["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty is not None:
            data["frequency_penalty"] = request.frequency_penalty

        response_data = await self._make_request("POST", "chat/completions", data)

        # Convert to our response format
        choices = []
        for choice_data in response_data.get("choices", []):
            message_data = choice_data.get("message", {})
            message = ChatMessage(
                role=message_data.get("role", "assistant"),
                content=message_data.get("content", "")
            )
            choice = Choice(
                index=choice_data.get("index", 0),
                message=message,
                finish_reason=choice_data.get("finish_reason")
            )
            choices.append(choice)

        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        ) if usage_data else None

        return ChatCompletionResponse(
            id=response_data.get("id", str(uuid.uuid4())),
            created=response_data.get("created", int(time.time())),
            model=response_data.get("model", "unknown"),
            provider=self.name,
            choices=choices,
            usage=usage
        )

    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate streaming chat completion using LMStudio.

        Args:
            request: Chat completion request with stream=True

        Yields:
            Stream chunks
        """
        # Convert to OpenAI-compatible format
        data = {
            "messages": [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ],
            "stream": True
        }

        # Add optional parameters
        if request.model:
            data["model"] = request.model
        if request.max_tokens:
            data["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            data["temperature"] = request.temperature
        if request.top_p is not None:
            data["top_p"] = request.top_p

        response = await self._make_request("POST", "chat/completions", data, stream=True)

        try:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    if data_str == '[DONE]':
                        break

                    try:
                        chunk_data = json.loads(data_str)
                        yield StreamChunk(
                            id=chunk_data.get("id", str(uuid.uuid4())),
                            created=chunk_data.get("created", int(time.time())),
                            model=chunk_data.get("model", "unknown"),
                            provider=self.name,
                            choices=chunk_data.get("choices", [])
                        )
                    except json.JSONDecodeError:
                        continue  # Skip malformed chunks

        finally:
            response.close()

    async def text_completion(
        self,
        request: CompletionRequest
    ) -> CompletionResponse:
        """Generate text completion using LMStudio.

        Args:
            request: Text completion request

        Returns:
            Text completion response
        """
        # Convert to OpenAI-compatible format
        data = {
            "prompt": request.prompt,
            "stream": False
        }

        # Add optional parameters
        if request.model:
            data["model"] = request.model
        if request.max_tokens:
            data["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            data["temperature"] = request.temperature
        if request.top_p is not None:
            data["top_p"] = request.top_p
        if request.stop:
            data["stop"] = request.stop
        if request.presence_penalty is not None:
            data["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty is not None:
            data["frequency_penalty"] = request.frequency_penalty

        response_data = await self._make_request("POST", "completions", data)

        # Convert to our response format
        choices = []
        for choice_data in response_data.get("choices", []):
            choice = Choice(
                index=choice_data.get("index", 0),
                text=choice_data.get("text", ""),
                finish_reason=choice_data.get("finish_reason")
            )
            choices.append(choice)

        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        ) if usage_data else None

        return CompletionResponse(
            id=response_data.get("id", str(uuid.uuid4())),
            created=response_data.get("created", int(time.time())),
            model=response_data.get("model", "unknown"),
            provider=self.name,
            choices=choices,
            usage=usage
        )

    async def generate_embeddings(
        self,
        request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """Generate embeddings using LMStudio.

        Args:
            request: Embedding request

        Returns:
            Embedding response

        Raises:
            ProviderError: LMStudio may not support embeddings
        """
        # Convert to OpenAI-compatible format
        data = {
            "input": request.input
        }

        if request.model:
            data["model"] = request.model

        try:
            response_data = await self._make_request("POST", "embeddings", data)
        except ProviderModelNotFoundError:
            # LMStudio may not support embeddings
            raise ProviderError(
                "LMStudio does not support embeddings or no embedding model loaded",
                self.name,
                "embeddings_not_supported"
            )

        # Convert to our response format
        embeddings = []
        for i, embedding_data in enumerate(response_data.get("data", [])):
            embedding = EmbeddingData(
                embedding=embedding_data.get("embedding", []),
                index=i
            )
            embeddings.append(embedding)

        usage_data = response_data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        ) if usage_data else None

        return EmbeddingResponse(
            data=embeddings,
            model=response_data.get("model", "unknown"),
            provider=self.name,
            usage=usage
        )

    async def list_models(self) -> List[ModelInfo]:
        """List available models in LMStudio.

        Returns:
            List of available models
        """
        try:
            response_data = await self._make_request("GET", "models")
        except ProviderConnectionError:
            # LMStudio may not be running
            return []

        models = []
        for model_data in response_data.get("data", []):
            model = ModelInfo(
                id=model_data.get("id", "unknown"),
                owned_by="lmstudio",
                provider=self.name,
                capabilities=["chat", "completion"],
                description=f"Local model hosted by LMStudio"
            )
            models.append(model)

        return models

    async def health_check(self) -> ProviderStatus:
        """Check LMStudio health status.

        Returns:
            Provider status information
        """
        start_time = time.time()

        try:
            models = await self.list_models()
            latency = (time.time() - start_time) * 1000

            return ProviderStatus(
                name=self.name,
                status="online",
                models_available=[model.id for model in models],
                latency_ms=latency,
                last_check=int(time.time())
            )

        except ProviderConnectionError as e:
            return ProviderStatus(
                name=self.name,
                status="offline",
                models_available=[],
                error_message=str(e),
                last_check=int(time.time())
            )

        except Exception as e:
            return ProviderStatus(
                name=self.name,
                status="error",
                models_available=[],
                error_message=str(e),
                last_check=int(time.time())
            )

    def supports_embeddings(self) -> bool:
        """LMStudio may not support embeddings."""
        return False  # Most LMStudio setups don't have embedding models

    def supports_functions(self) -> bool:
        """LMStudio typically doesn't support function calling."""
        return False

    def get_context_length(self, model_id: str) -> Optional[int]:
        """Get context length for LMStudio model.

        Args:
            model_id: Model identifier

        Returns:
            Estimated context length based on model name
        """
        model_lower = model_id.lower()

        # Common model context lengths
        if "llama-2" in model_lower:
            if "32k" in model_lower:
                return 32768
            else:
                return 4096
        elif "codellama" in model_lower:
            if "34b" in model_lower:
                return 16384
            else:
                return 4096
        elif "mistral" in model_lower:
            if "7b" in model_lower:
                return 8192
            else:
                return 4096
        elif "vicuna" in model_lower:
            return 2048
        else:
            # Default assumption for local models
            return 4096