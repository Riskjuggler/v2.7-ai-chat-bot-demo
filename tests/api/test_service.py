"""Tests for LLM service layer."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from src.api.service import LLMService


@pytest.fixture
def service():
    """Create LLMService instance."""
    return LLMService()


class TestLLMService:
    """Tests for LLMService."""

    @pytest.mark.asyncio
    async def test_chat_success_dict_response(self, service):
        """Test successful chat with dict response from LLM."""
        # Mock the response object
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.content = "The capital of France is Paris."
        mock_response.model = "gpt-3.5-turbo"

        with patch.object(
            service.llm_service, "chat_completion", return_value=mock_response
        ):
            response_text, model_name, timestamp = await service.chat(
                "What is the capital of France?"
            )

            assert response_text == "The capital of France is Paris."
            assert model_name == "gpt-3.5-turbo"
            assert isinstance(timestamp, datetime)

    @pytest.mark.asyncio
    async def test_chat_success_string_response(self, service):
        """Test successful chat with string response from LLM."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.content = "The capital of France is Paris."
        mock_response.model = None

        with patch.object(
            service.llm_service, "chat_completion", return_value=mock_response
        ):
            response_text, model_name, timestamp = await service.chat(
                "What is the capital of France?"
            )

            assert response_text == "The capital of France is Paris."
            assert model_name == service.provider
            assert isinstance(timestamp, datetime)

    @pytest.mark.asyncio
    async def test_chat_timeout(self, service):
        """Test chat timeout handling."""
        with patch.object(
            service.llm_service,
            "chat_completion",
            side_effect=TimeoutError("Request timeout"),
        ):
            with pytest.raises(TimeoutError) as exc:
                await service.chat("test message")

            assert "LLM request timeout" in str(exc.value)

    @pytest.mark.asyncio
    async def test_chat_connection_error(self, service):
        """Test chat connection error handling."""
        with patch.object(
            service.llm_service,
            "chat_completion",
            side_effect=ConnectionError("Cannot connect to LLM service"),
        ):
            with pytest.raises(ConnectionError) as exc:
                await service.chat("test message")

            assert "Cannot connect to LLM service" in str(exc.value)

    @pytest.mark.asyncio
    async def test_chat_generic_error(self, service):
        """Test chat generic error handling."""
        with patch.object(
            service.llm_service,
            "chat_completion",
            side_effect=Exception("Unknown error"),
        ):
            with pytest.raises(ValueError) as exc:
                await service.chat("test message")

            assert "LLM error" in str(exc.value)

    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """Test health check when LLM is available."""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.content = "test"

        with patch.object(
            service.llm_service, "chat_completion", return_value=mock_response
        ):
            is_available = await service.health_check()
            assert is_available is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, service):
        """Test health check when LLM is unavailable."""
        with patch.object(
            service.llm_service,
            "chat_completion",
            side_effect=ConnectionError("Service down"),
        ):
            is_available = await service.health_check()
            assert is_available is False

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, service):
        """Test health check when LLM times out."""
        with patch.object(
            service.llm_service, "chat_completion", side_effect=TimeoutError("Timeout")
        ):
            is_available = await service.health_check()
            assert is_available is False


class TestLLMServiceInit:
    """Tests for LLMService initialization."""

    def test_initialization(self):
        """Test LLMService initializes with correct settings."""
        service = LLMService()

        assert service.provider == "lmstudio"
        assert service.llm_service is not None
