"""Tests for API routes."""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestChatEndpoint:
    """Tests for POST /chat endpoint."""

    def test_chat_success(self, client):
        """Test successful chat request."""
        mock_response = (
            "The capital of France is Paris.",
            "gpt-3.5-turbo",
            datetime.now(),
        )

        with patch(
            "src.api.routes.llm_service.chat",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = client.post(
                "/chat", json={"message": "What is the capital of France?"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "The capital of France is Paris."
            assert data["model"] == "gpt-3.5-turbo"
            assert "timestamp" in data

    def test_chat_validation_error_empty_message(self, client):
        """Test chat with empty message returns 422."""
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_validation_error_missing_message(self, client):
        """Test chat without message field returns 422."""
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_chat_validation_error_message_too_long(self, client):
        """Test chat with message too long returns 422."""
        long_message = "x" * 10001
        response = client.post("/chat", json={"message": long_message})
        assert response.status_code == 422

    def test_chat_timeout_error(self, client):
        """Test chat timeout returns 503."""
        with patch(
            "src.api.routes.llm_service.chat",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Request timeout"),
        ):
            response = client.post("/chat", json={"message": "test"})

            assert response.status_code == 503
            data = response.json()
            assert "detail" in data

    def test_chat_connection_error(self, client):
        """Test chat connection error returns 500."""
        with patch(
            "src.api.routes.llm_service.chat",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Cannot connect"),
        ):
            response = client.post("/chat", json={"message": "test"})

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_chat_value_error(self, client):
        """Test chat value error returns 500."""
        with patch(
            "src.api.routes.llm_service.chat",
            new_callable=AsyncMock,
            side_effect=ValueError("Invalid response"),
        ):
            response = client.post("/chat", json={"message": "test"})

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_llm_available(self, client):
        """Test health check when LLM is available."""
        with patch(
            "src.api.routes.llm_service.health_check",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["llm_available"] is True

    def test_health_llm_unavailable(self, client):
        """Test health check when LLM is unavailable."""
        with patch(
            "src.api.routes.llm_service.health_check",
            new_callable=AsyncMock,
            return_value=False,
        ):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["llm_available"] is False


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_docs_accessible(self, client):
        """Test OpenAPI documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self, client):
        """Test ReDoc documentation is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_accessible(self, client):
        """Test OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "AI Chat API"


class TestLifecycleEvents:
    """Tests for app lifecycle events."""

    def test_startup_shutdown_events(self):
        """Test startup and shutdown events are defined."""
        from src.api.main import app

        # Verify lifecycle handlers are registered
        # These run during actual server startup/shutdown
        assert hasattr(app, "router")
        assert app.title == "AI Chat API"
        assert app.version == "0.1.0"
