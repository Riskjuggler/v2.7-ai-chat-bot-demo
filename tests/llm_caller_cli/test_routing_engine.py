"""Tests for the routing engine."""

import pytest
from unittest.mock import Mock, patch
from llm_caller_cli.src.models.request_models import (
    TaskType,
    ChatCompletionRequest,
    ChatMessage,
    MessageRole,
    CompletionRequest,
    EmbeddingRequest
)
from llm_caller_cli.src.core.routing_engine import RoutingEngine
from llm_caller_cli.src.config.model_capabilities import ModelCapabilityRegistry


class TestRoutingEngine:
    """Test cases for the routing engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.routing_engine = RoutingEngine()
        self.available_providers = ["lmstudio", "openai"]

    def test_detect_task_type_code_analysis(self):
        """Test task type detection for code analysis."""
        test_cases = [
            "analyze this Python function",
            "explain what this code does",
            "review the implementation of this method",
            "understand this algorithm"
        ]

        for text in test_cases:
            task_type = self.routing_engine.detect_task_type(text)
            assert task_type == TaskType.CODE_ANALYSIS

    def test_detect_task_type_code_generation(self):
        """Test task type detection for code generation."""
        test_cases = [
            "write a function to sort an array",
            "create a class for data processing",
            "implement a binary search algorithm",
            "generate code for API endpoint"
        ]

        for text in test_cases:
            task_type = self.routing_engine.detect_task_type(text)
            assert task_type == TaskType.CODE_GENERATION

    def test_detect_task_type_document_analysis(self):
        """Test task type detection for document analysis."""
        test_cases = [
            "analyze this document for key insights",
            "examine the content of this paper",
            "what does this text contain",
            "extract information from this document"
        ]

        for text in test_cases:
            task_type = self.routing_engine.detect_task_type(text)
            assert task_type == TaskType.DOCUMENT_ANALYSIS

    def test_detect_task_type_general(self):
        """Test task type detection for general queries."""
        test_cases = [
            "hello, how are you?",
            "what's the weather like?",
            "tell me a joke",
            "random question here"
        ]

        for text in test_cases:
            task_type = self.routing_engine.detect_task_type(text)
            assert task_type == TaskType.GENERAL

    def test_route_chat_completion_explicit_model(self):
        """Test routing when model is explicitly specified."""
        messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
        request = ChatCompletionRequest(
            messages=messages,
            model="gpt-4"
        )

        decision = self.routing_engine.route_chat_completion(
            request, self.available_providers
        )

        assert decision.selected_model == "gpt-4"
        assert decision.selected_provider == "openai"
        assert decision.confidence_score == 1.0

    def test_route_chat_completion_task_based(self):
        """Test routing based on task type."""
        messages = [ChatMessage(role=MessageRole.USER, content="write a Python function")]
        request = ChatCompletionRequest(
            messages=messages,
            task_type=TaskType.CODE_GENERATION
        )

        decision = self.routing_engine.route_chat_completion(
            request, self.available_providers
        )

        assert decision.task_type == TaskType.CODE_GENERATION
        assert decision.selected_model is not None
        assert decision.selected_provider in self.available_providers

    def test_route_chat_completion_prefer_local(self):
        """Test routing with local preference."""
        messages = [ChatMessage(role=MessageRole.USER, content="Hello world")]
        request = ChatCompletionRequest(
            messages=messages,
            prefer_local=True
        )

        decision = self.routing_engine.route_chat_completion(
            request, self.available_providers
        )

        # Should prefer LMStudio if available
        assert decision.selected_provider == "lmstudio"

    def test_route_completion_request(self):
        """Test routing for completion requests."""
        request = CompletionRequest(
            prompt="Complete this sentence:",
            task_type=TaskType.CREATIVE_WRITING
        )

        decision = self.routing_engine.route_completion(
            request, self.available_providers
        )

        assert decision.task_type == TaskType.CREATIVE_WRITING
        assert decision.selected_model is not None
        assert decision.selected_provider in self.available_providers

    def test_route_embedding_request(self):
        """Test routing for embedding requests."""
        request = EmbeddingRequest(
            input=["text to embed"]
        )

        # Mock available embedding models
        with patch.object(
            self.routing_engine.capability_registry,
            'get_all_capabilities'
        ) as mock_capabilities:
            mock_capability = Mock()
            mock_capability.category.value = "embedding"
            mock_capability.provider = "openai"
            mock_capability.model_id = "text-embedding-ada-002"
            mock_capability.quality_score = 0.85

            mock_capabilities.return_value = {
                "text-embedding-ada-002": mock_capability
            }

            decision = self.routing_engine.route_embedding(
                request, self.available_providers
            )

            assert decision.selected_model == "text-embedding-ada-002"
            assert decision.selected_provider == "openai"

    def test_routing_with_no_available_providers(self):
        """Test routing when no providers are available."""
        messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
        request = ChatCompletionRequest(messages=messages)

        with pytest.raises(ValueError, match="No suitable model found"):
            self.routing_engine.route_chat_completion(request, [])

    def test_get_routing_statistics(self):
        """Test routing statistics generation."""
        stats = self.routing_engine.get_routing_statistics()

        assert "total_models" in stats
        assert "providers" in stats
        assert "categories" in stats
        assert "models_by_provider" in stats
        assert "task_coverage" in stats

        # Check that we have expected providers
        assert "openai" in stats["providers"]
        assert "lmstudio" in stats["providers"]

        # Check task coverage
        assert TaskType.CODE_ANALYSIS.value in stats["task_coverage"]
        assert TaskType.GENERAL.value in stats["task_coverage"]

    def test_routing_decision_structure(self):
        """Test that routing decisions have required fields."""
        messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
        request = ChatCompletionRequest(messages=messages)

        decision = self.routing_engine.route_chat_completion(
            request, self.available_providers
        )

        # Check required fields
        assert hasattr(decision, 'selected_model')
        assert hasattr(decision, 'selected_provider')
        assert hasattr(decision, 'reasoning')
        assert hasattr(decision, 'task_type')
        assert hasattr(decision, 'confidence_score')
        assert hasattr(decision, 'fallback_models')

        # Check data types
        assert isinstance(decision.selected_model, str)
        assert isinstance(decision.selected_provider, str)
        assert isinstance(decision.reasoning, str)
        assert isinstance(decision.confidence_score, float)
        assert isinstance(decision.fallback_models, list)

        # Check value ranges
        assert 0.0 <= decision.confidence_score <= 1.0

    def test_context_length_routing(self):
        """Test routing based on context length requirements."""
        # Create a very long message
        long_content = "word " * 10000  # Simulate large context requirement
        messages = [ChatMessage(role=MessageRole.USER, content=long_content)]
        request = ChatCompletionRequest(messages=messages)

        decision = self.routing_engine.route_chat_completion(
            request, self.available_providers
        )

        # Should select a model with sufficient context length
        capability = self.routing_engine.capability_registry.get_capability(
            decision.selected_model
        )
        assert capability is not None
        # The estimated token count should be within the model's context limit
        estimated_tokens = self.routing_engine._estimate_tokens(long_content)
        assert estimated_tokens <= capability.context_length