"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
)


class TestChatRequest:
    """Tests for ChatRequest schema."""

    def test_valid_request(self):
        """Test valid chat request serialization."""
        request = ChatRequest(message="Hello")
        assert request.message == "Hello"

    def test_message_too_short(self):
        """Test message length validation (minimum)."""
        with pytest.raises(ValidationError) as exc:
            ChatRequest(message="")
        assert "at least 1 character" in str(exc.value).lower()

    def test_message_too_long(self):
        """Test message length validation (maximum)."""
        long_message = "x" * 10001
        with pytest.raises(ValidationError) as exc:
            ChatRequest(message=long_message)
        assert "at most 10000 characters" in str(exc.value).lower()

    def test_message_required(self):
        """Test message field is required."""
        with pytest.raises(ValidationError) as exc:
            ChatRequest()
        assert "field required" in str(exc.value).lower()


class TestChatResponse:
    """Tests for ChatResponse schema."""

    def test_valid_response(self):
        """Test valid chat response serialization."""
        now = datetime.now()
        response = ChatResponse(
            response="Hello there!", model="gpt-3.5-turbo", timestamp=now
        )
        assert response.response == "Hello there!"
        assert response.model == "gpt-3.5-turbo"
        assert response.timestamp == now

    def test_all_fields_required(self):
        """Test all fields are required."""
        with pytest.raises(ValidationError):
            ChatResponse()


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_error_only(self):
        """Test error response with error only."""
        error = ErrorResponse(error="Something went wrong")
        assert error.error == "Something went wrong"
        assert error.detail is None

    def test_error_with_detail(self):
        """Test error response with detail."""
        error = ErrorResponse(error="Timeout", detail="Connection timeout after 30s")
        assert error.error == "Timeout"
        assert error.detail == "Connection timeout after 30s"


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_healthy_with_llm(self):
        """Test health response when LLM is available."""
        health = HealthResponse(status="healthy", llm_available=True)
        assert health.status == "healthy"
        assert health.llm_available is True

    def test_healthy_without_llm(self):
        """Test health response when LLM is unavailable."""
        health = HealthResponse(status="healthy", llm_available=False)
        assert health.status == "healthy"
        assert health.llm_available is False
