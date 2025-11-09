"""Tests for the LMStudio provider."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import aiohttp
from llm_caller_cli.src.providers.lmstudio_provider import LMStudioProvider
from llm_caller_cli.src.providers.base_provider import (
    ProviderError,
    ProviderConnectionError,
    ProviderTimeoutError,
    ProviderModelNotFoundError
)
from llm_caller_cli.src.models.request_models import (
    ChatCompletionRequest,
    ChatMessage,
    MessageRole,
    CompletionRequest,
    EmbeddingRequest
)


class TestLMStudioProvider:
    """Test cases for the LMStudio provider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "base_url": "http://localhost:1234/v1",
            "timeout": 30.0,
            "max_retries": 3
        }
        self.provider = LMStudioProvider(self.config)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test provider initialization."""
        await self.provider.initialize()
        assert self.provider.session is not None
        await self.provider.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test provider cleanup."""
        await self.provider.initialize()
        await self.provider.cleanup()
        # Session should be closed after cleanup

    @pytest.mark.asyncio
    async def test_chat_completion_success(self):
        """Test successful chat completion."""
        # Mock response data
        mock_response_data = {
            "id": "test-id",
            "created": 1234567890,
            "model": "llama-2-7b-chat",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18
            }
        }

        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
            request = ChatCompletionRequest(messages=messages)

            response = await self.provider.chat_completion(request)

            assert response.id == "test-id"
            assert response.model == "llama-2-7b-chat"
            assert response.provider == "lmstudio"
            assert len(response.choices) == 1
            assert response.choices[0].message.content == "Hello! How can I help you?"
            assert response.usage.total_tokens == 18

    @pytest.mark.asyncio
    async def test_chat_completion_with_parameters(self):
        """Test chat completion with additional parameters."""
        mock_response_data = {
            "id": "test-id",
            "created": 1234567890,
            "model": "llama-2-7b-chat",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Response"}}]
        }

        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
            request = ChatCompletionRequest(
                messages=messages,
                model="llama-2-7b-chat",
                temperature=0.7,
                max_tokens=100,
                top_p=0.9
            )

            await self.provider.chat_completion(request)

            # Check that parameters were passed correctly
            mock_request.assert_called_once()
            # _make_request is called with ("POST", "chat/completions", data)
            # The third positional argument is the data dict
            call_args, call_kwargs = mock_request.call_args
            assert len(call_args) == 3
            data = call_args[2]  # Third positional argument is the data
            assert data['temperature'] == 0.7
            assert data['max_tokens'] == 100
            assert data['top_p'] == 0.9

    @pytest.mark.asyncio
    async def test_text_completion_success(self):
        """Test successful text completion."""
        mock_response_data = {
            "id": "test-id",
            "created": 1234567890,
            "model": "llama-2-7b",
            "choices": [
                {
                    "index": 0,
                    "text": "This is a completion.",
                    "finish_reason": "stop"
                }
            ]
        }

        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            request = CompletionRequest(prompt="Complete this sentence:")
            response = await self.provider.text_completion(request)

            assert response.id == "test-id"
            assert response.model == "llama-2-7b"
            assert response.provider == "lmstudio"
            assert len(response.choices) == 1
            assert response.choices[0].text == "This is a completion."

    @pytest.mark.asyncio
    async def test_list_models_success(self):
        """Test successful model listing."""
        mock_response_data = {
            "data": [
                {
                    "id": "llama-2-7b-chat",
                    "object": "model",
                    "owned_by": "lmstudio"
                },
                {
                    "id": "codellama-7b-instruct",
                    "object": "model",
                    "owned_by": "lmstudio"
                }
            ]
        }

        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            models = await self.provider.list_models()

            assert len(models) == 2
            assert models[0].id == "llama-2-7b-chat"
            assert models[0].provider == "lmstudio"
            assert models[1].id == "codellama-7b-instruct"

    @pytest.mark.asyncio
    async def test_list_models_connection_error(self):
        """Test model listing when LMStudio is not running."""
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = ProviderConnectionError("Connection failed", "lmstudio")

            models = await self.provider.list_models()

            # Should return empty list when connection fails
            assert models == []

    @pytest.mark.asyncio
    async def test_health_check_online(self):
        """Test health check when LMStudio is online."""
        mock_models = [Mock(id="llama-2-7b-chat")]

        with patch.object(self.provider, 'list_models', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_models

            status = await self.provider.health_check()

            assert status.name == "lmstudio"
            assert status.status == "online"
            assert status.models_available == ["llama-2-7b-chat"]
            assert status.latency_ms is not None

    @pytest.mark.asyncio
    async def test_health_check_offline(self):
        """Test health check when LMStudio is offline."""
        with patch.object(self.provider, 'list_models', new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = ProviderConnectionError("Connection failed", "lmstudio")

            status = await self.provider.health_check()

            assert status.name == "lmstudio"
            assert status.status == "offline"
            assert status.models_available == []
            assert "Connection failed" in status.error_message

    @pytest.mark.asyncio
    async def test_generate_embeddings_not_supported(self):
        """Test embedding generation when not supported."""
        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = ProviderModelNotFoundError("Endpoint not found", "lmstudio")

            request = EmbeddingRequest(input=["text to embed"])

            with pytest.raises(ProviderError, match="does not support embeddings"):
                await self.provider.generate_embeddings(request)

    @pytest.mark.asyncio
    async def test_streaming_chat_completion(self):
        """Test streaming chat completion."""
        # Mock streaming response
        mock_chunks = [
            'data: {"id":"test","choices":[{"delta":{"content":"Hello"}}]}\n\n',
            'data: {"id":"test","choices":[{"delta":{"content":" world"}}]}\n\n',
            'data: [DONE]\n\n'
        ]

        # Create proper async iterator for streaming
        class AsyncIterator:
            def __init__(self, items):
                self.items = items
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                item = self.items[self.index]
                self.index += 1
                return item

        mock_response = Mock()
        mock_response.content = AsyncIterator([chunk.encode() for chunk in mock_chunks])
        mock_response.close = AsyncMock()

        with patch.object(self.provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
            request = ChatCompletionRequest(messages=messages, stream=True)

            chunks = []
            async for chunk in self.provider.chat_completion_stream(request):
                chunks.append(chunk)

            assert len(chunks) == 2  # Should exclude [DONE] chunk
            assert chunks[0].provider == "lmstudio"

    @pytest.mark.asyncio
    async def test_make_request_timeout(self):
        """Test request timeout handling."""
        await self.provider.initialize()

        with patch.object(self.provider.session, 'request') as mock_request:
            # ClientTimeout is not an exception, it's a config class
            mock_request.side_effect = asyncio.TimeoutError()

            with pytest.raises(ProviderTimeoutError):
                await self.provider._make_request("GET", "models")

        await self.provider.cleanup()

    @pytest.mark.asyncio
    async def test_make_request_connection_error(self):
        """Test connection error handling."""
        await self.provider.initialize()

        with patch.object(self.provider.session, 'request') as mock_request:
            # Create proper connection error with required message argument
            mock_request.side_effect = aiohttp.ClientConnectionError("Connection failed")

            with pytest.raises(ProviderConnectionError):
                await self.provider._make_request("GET", "models")

        await self.provider.cleanup()

    @pytest.mark.asyncio
    async def test_make_request_404_error(self):
        """Test 404 error handling."""
        await self.provider.initialize()

        mock_response = Mock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        with patch.object(self.provider.session, 'request') as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(ProviderModelNotFoundError):
                await self.provider._make_request("GET", "nonexistent")

        await self.provider.cleanup()

    def test_get_context_length(self):
        """Test context length estimation for different models."""
        test_cases = [
            ("llama-2-7b-chat", 4096),
            ("llama-2-32k-chat", 32768),
            ("codellama-34b-instruct", 16384),
            ("mistral-7b-instruct", 8192),
            ("unknown-model", 4096)  # Default
        ]

        for model_id, expected_length in test_cases:
            context_length = self.provider.get_context_length(model_id)
            assert context_length == expected_length

    def test_supports_capabilities(self):
        """Test capability flags."""
        assert self.provider.supports_chat() is True
        assert self.provider.supports_completion() is True
        assert self.provider.supports_embeddings() is False
        assert self.provider.supports_functions() is False
        assert self.provider.supports_streaming() is True

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with self.provider as provider:
            assert provider.session is not None

        # Session should be cleaned up after context exit