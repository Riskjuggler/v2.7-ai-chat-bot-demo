"""
TDD Tests for model capabilities registry.

These tests drive the model capability system design and ensure proper
model routing, capability tracking, and cost estimation.
"""

import pytest
from llm_caller_cli.src.config.model_capabilities import (
    ModelCapabilityRegistry,
    ModelCapability,
    ModelCategory
)
from llm_caller_cli.src.models.request_models import TaskType


class TestModelCapability:
    """Test the ModelCapability dataclass."""

    def test_model_capability_creation(self):
        """Test creating a ModelCapability with all fields."""
        capability = ModelCapability(
            model_id="gpt-4",
            provider="openai",
            category=ModelCategory.GENERAL_PURPOSE,
            supported_tasks={TaskType.GENERAL, TaskType.CODE_ANALYSIS},
            context_length=128000,
            cost_per_input_token=0.00003,
            cost_per_output_token=0.00006,
            quality_score=0.95,
            speed_score=0.7,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=False,
            max_output_tokens=4096,
            description="Most capable GPT-4 model"
        )

        assert capability.model_id == "gpt-4"
        assert capability.provider == "openai"
        assert capability.category == ModelCategory.GENERAL_PURPOSE
        assert TaskType.GENERAL in capability.supported_tasks
        assert TaskType.CODE_ANALYSIS in capability.supported_tasks
        assert capability.context_length == 128000
        assert capability.cost_per_input_token == 0.00003
        assert capability.cost_per_output_token == 0.00006
        assert capability.quality_score == 0.95
        assert capability.speed_score == 0.7
        assert capability.supports_streaming is True
        assert capability.supports_functions is True
        assert capability.supports_vision is False
        assert capability.max_output_tokens == 4096
        assert capability.description == "Most capable GPT-4 model"

    def test_model_capability_defaults(self):
        """Test ModelCapability default values."""
        capability = ModelCapability(
            model_id="test-model",
            provider="test-provider",
            category=ModelCategory.LOCAL,
            supported_tasks={TaskType.GENERAL},
            context_length=4096
        )

        # Check defaults
        assert capability.cost_per_input_token is None
        assert capability.cost_per_output_token is None
        assert capability.quality_score == 1.0
        assert capability.speed_score == 1.0
        assert capability.supports_streaming is True
        assert capability.supports_functions is False
        assert capability.supports_vision is False
        assert capability.max_output_tokens is None
        assert capability.description == ""


class TestModelCapabilityRegistryInitialization:
    """Test ModelCapabilityRegistry initialization."""

    def test_registry_initializes_with_default_capabilities(self):
        """Test that registry initializes with default model capabilities."""
        registry = ModelCapabilityRegistry()

        # Should have some default capabilities
        capabilities = registry.get_all_capabilities()
        assert len(capabilities) > 0

        # Should have OpenAI models
        assert "gpt-4" in capabilities
        assert "gpt-3.5-turbo" in capabilities
        assert "text-embedding-ada-002" in capabilities

        # Should have Anthropic models
        assert "claude-3-opus-20240229" in capabilities
        assert "claude-3-sonnet-20240229" in capabilities

        # Should have local models
        assert "llama-2-7b-chat" in capabilities
        assert "codellama-7b-instruct" in capabilities

    def test_registry_gpt4_capability_correct(self):
        """Test that GPT-4 capability is configured correctly."""
        registry = ModelCapabilityRegistry()
        gpt4 = registry.get_capability("gpt-4")

        assert gpt4 is not None
        assert gpt4.provider == "openai"
        assert gpt4.category == ModelCategory.GENERAL_PURPOSE
        assert gpt4.context_length == 128000
        assert gpt4.supports_functions is True
        assert TaskType.CODE_ANALYSIS in gpt4.supported_tasks
        assert TaskType.DOCUMENT_ANALYSIS in gpt4.supported_tasks

    def test_registry_claude_opus_capability_correct(self):
        """Test that Claude Opus capability is configured correctly."""
        registry = ModelCapabilityRegistry()
        claude = registry.get_capability("claude-3-opus-20240229")

        assert claude is not None
        assert claude.provider == "anthropic"
        assert claude.category == ModelCategory.REASONING
        assert claude.context_length == 200000
        assert claude.supports_vision is True
        assert TaskType.MATH_REASONING in claude.supported_tasks

    def test_registry_local_model_capability_correct(self):
        """Test that local model capability is configured correctly."""
        registry = ModelCapabilityRegistry()
        llama = registry.get_capability("llama-2-7b-chat")

        assert llama is not None
        assert llama.provider == "lmstudio"
        assert llama.category == ModelCategory.LOCAL
        assert llama.supports_functions is False
        assert llama.cost_per_input_token is None  # Local models have no cost


class TestModelCapabilityRegistryManagement:
    """Test capability registration and retrieval."""

    def test_register_capability(self):
        """Test registering a new capability."""
        registry = ModelCapabilityRegistry()

        new_capability = ModelCapability(
            model_id="test-model",
            provider="test-provider",
            category=ModelCategory.LOCAL,
            supported_tasks={TaskType.GENERAL},
            context_length=4096,
            quality_score=0.8
        )

        registry.register_capability(new_capability)

        # Should be able to retrieve it
        retrieved = registry.get_capability("test-model")
        assert retrieved is not None
        assert retrieved.model_id == "test-model"
        assert retrieved.provider == "test-provider"
        assert retrieved.quality_score == 0.8

    def test_register_capability_overwrites_existing(self):
        """Test that registering overwrites existing capability."""
        registry = ModelCapabilityRegistry()

        # Register initial capability
        capability1 = ModelCapability(
            model_id="test-model",
            provider="provider1",
            category=ModelCategory.LOCAL,
            supported_tasks={TaskType.GENERAL},
            context_length=4096,
            quality_score=0.7
        )
        registry.register_capability(capability1)

        # Register updated capability
        capability2 = ModelCapability(
            model_id="test-model",
            provider="provider2",
            category=ModelCategory.GENERAL_PURPOSE,
            supported_tasks={TaskType.CODE_ANALYSIS},
            context_length=8192,
            quality_score=0.9
        )
        registry.register_capability(capability2)

        # Should have the updated version
        retrieved = registry.get_capability("test-model")
        assert retrieved.provider == "provider2"
        assert retrieved.quality_score == 0.9
        assert retrieved.context_length == 8192

    def test_get_capability_missing_model(self):
        """Test getting capability for non-existent model."""
        registry = ModelCapabilityRegistry()

        capability = registry.get_capability("nonexistent-model")
        assert capability is None

    def test_get_all_capabilities_returns_copy(self):
        """Test that get_all_capabilities returns a copy."""
        registry = ModelCapabilityRegistry()

        capabilities1 = registry.get_all_capabilities()
        capabilities2 = registry.get_all_capabilities()

        # Should be different objects
        assert capabilities1 is not capabilities2
        # But with same content
        assert capabilities1 == capabilities2


class TestModelCapabilityRegistryTaskFiltering:
    """Test filtering capabilities by task type."""

    def test_get_models_for_task_code_analysis(self):
        """Test getting models that support code analysis."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_for_task(TaskType.CODE_ANALYSIS)

        # Should have multiple models
        assert len(models) > 0

        # All returned models should support code analysis
        for model in models:
            assert TaskType.CODE_ANALYSIS in model.supported_tasks

        # Should include GPT-4, Claude Opus, and CodeLlama models
        model_ids = [model.model_id for model in models]
        assert "gpt-4" in model_ids
        assert "claude-3-opus-20240229" in model_ids
        assert "codellama-7b-instruct" in model_ids

    def test_get_models_for_task_embeddings(self):
        """Test getting models for document analysis (embeddings)."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_for_task(TaskType.DOCUMENT_ANALYSIS)

        # Should include embedding models and general models
        model_ids = [model.model_id for model in models]
        assert "text-embedding-ada-002" in model_ids
        assert "gpt-4" in model_ids  # General models also support document analysis

    def test_get_models_for_task_creative_writing(self):
        """Test getting models for creative writing."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_for_task(TaskType.CREATIVE_WRITING)

        # Should have various models that support creative writing
        model_ids = [model.model_id for model in models]
        assert "gpt-4" in model_ids
        assert "claude-3-sonnet-20240229" in model_ids
        assert "llama-2-7b-chat" in model_ids

    def test_get_models_for_task_no_matches(self):
        """Test getting models for task with no supporting models."""
        registry = ModelCapabilityRegistry()

        # Clear all capabilities
        registry._capabilities = {}

        models = registry.get_models_for_task(TaskType.CODE_ANALYSIS)
        assert len(models) == 0


class TestModelCapabilityRegistryProviderFiltering:
    """Test filtering capabilities by provider."""

    def test_get_models_by_provider_openai(self):
        """Test getting OpenAI models."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_provider("openai")

        # Should have multiple OpenAI models
        assert len(models) > 0

        # All should be from OpenAI
        for model in models:
            assert model.provider == "openai"

        # Should include expected models
        model_ids = [model.model_id for model in models]
        assert "gpt-4" in model_ids
        assert "gpt-3.5-turbo" in model_ids
        assert "text-embedding-ada-002" in model_ids

    def test_get_models_by_provider_anthropic(self):
        """Test getting Anthropic models."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_provider("anthropic")

        # All should be from Anthropic
        for model in models:
            assert model.provider == "anthropic"

        # Should include Claude models
        model_ids = [model.model_id for model in models]
        assert "claude-3-opus-20240229" in model_ids
        assert "claude-3-sonnet-20240229" in model_ids

    def test_get_models_by_provider_lmstudio(self):
        """Test getting LMStudio (local) models."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_provider("lmstudio")

        # All should be from LMStudio
        for model in models:
            assert model.provider == "lmstudio"

        # Should include local models
        model_ids = [model.model_id for model in models]
        assert "llama-2-7b-chat" in model_ids
        assert "codellama-7b-instruct" in model_ids

    def test_get_models_by_provider_nonexistent(self):
        """Test getting models from non-existent provider."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_provider("nonexistent-provider")
        assert len(models) == 0


class TestModelCapabilityRegistryCategoryFiltering:
    """Test filtering capabilities by category."""

    def test_get_models_by_category_general_purpose(self):
        """Test getting general purpose models."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_category(ModelCategory.GENERAL_PURPOSE)

        # All should be general purpose
        for model in models:
            assert model.category == ModelCategory.GENERAL_PURPOSE

        # Should include GPT-4 and Claude Sonnet
        model_ids = [model.model_id for model in models]
        assert "gpt-4" in model_ids
        assert "claude-3-sonnet-20240229" in model_ids

    def test_get_models_by_category_code_specialized(self):
        """Test getting code specialized models."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_category(ModelCategory.CODE_SPECIALIZED)

        # All should be code specialized
        for model in models:
            assert model.category == ModelCategory.CODE_SPECIALIZED

        # Should include CodeLlama models
        model_ids = [model.model_id for model in models]
        assert "codellama-7b-instruct" in model_ids
        assert "codellama-13b-instruct" in model_ids

    def test_get_models_by_category_embedding(self):
        """Test getting embedding models."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_category(ModelCategory.EMBEDDING)

        # All should be embedding models
        for model in models:
            assert model.category == ModelCategory.EMBEDDING

        # Should include Ada embeddings
        model_ids = [model.model_id for model in models]
        assert "text-embedding-ada-002" in model_ids

    def test_get_models_by_category_local(self):
        """Test getting local models."""
        registry = ModelCapabilityRegistry()

        models = registry.get_models_by_category(ModelCategory.LOCAL)

        # All should be local models
        for model in models:
            assert model.category == ModelCategory.LOCAL
            assert model.provider == "lmstudio"


class TestModelCapabilityRegistryBestModelSelection:
    """Test best model selection logic."""

    def test_get_best_model_for_task_basic(self):
        """Test getting best model for a task without filters."""
        registry = ModelCapabilityRegistry()

        best = registry.get_best_model_for_task(TaskType.CODE_ANALYSIS)

        assert best is not None
        assert TaskType.CODE_ANALYSIS in best.supported_tasks
        # Should be high quality (default sort)
        assert best.quality_score >= 0.8

    def test_get_best_model_for_task_prefer_local(self):
        """Test getting best model with local preference."""
        registry = ModelCapabilityRegistry()

        best = registry.get_best_model_for_task(
            TaskType.CODE_GENERATION,
            prefer_local=True
        )

        assert best is not None
        assert TaskType.CODE_GENERATION in best.supported_tasks
        # Should prefer local model
        assert best.category == ModelCategory.LOCAL or best.category == ModelCategory.CODE_SPECIALIZED

    def test_get_best_model_for_task_quality_filter(self):
        """Test getting best model with quality filter."""
        registry = ModelCapabilityRegistry()

        best = registry.get_best_model_for_task(
            TaskType.GENERAL,
            min_quality_score=0.9
        )

        assert best is not None
        assert best.quality_score >= 0.9

    def test_get_best_model_for_task_speed_filter(self):
        """Test getting best model with speed filter."""
        registry = ModelCapabilityRegistry()

        best = registry.get_best_model_for_task(
            TaskType.GENERAL,
            min_speed_score=0.8
        )

        assert best is not None
        assert best.speed_score >= 0.8

    def test_get_best_model_for_task_cost_filter(self):
        """Test getting best model with cost filter."""
        registry = ModelCapabilityRegistry()

        best = registry.get_best_model_for_task(
            TaskType.GENERAL,
            max_cost_per_token=0.00001
        )

        assert best is not None
        # Should either have no cost (local) or be under limit
        if best.cost_per_output_token is not None:
            assert best.cost_per_output_token <= 0.00001

    def test_get_best_model_for_task_context_filter(self):
        """Test getting best model with context length requirement."""
        registry = ModelCapabilityRegistry()

        best = registry.get_best_model_for_task(
            TaskType.DOCUMENT_ANALYSIS,
            required_context_length=100000
        )

        assert best is not None
        assert best.context_length >= 100000

    def test_get_best_model_for_task_no_matches(self):
        """Test getting best model when no models match criteria."""
        registry = ModelCapabilityRegistry()

        best = registry.get_best_model_for_task(
            TaskType.GENERAL,
            min_quality_score=2.0  # Impossible requirement
        )

        assert best is None

    def test_get_best_model_for_task_unsupported_task(self):
        """Test getting best model for unsupported task."""
        registry = ModelCapabilityRegistry()

        # Clear all capabilities
        registry._capabilities = {}

        best = registry.get_best_model_for_task(TaskType.CODE_ANALYSIS)
        assert best is None


class TestModelCapabilityRegistryCostEstimation:
    """Test cost estimation functionality."""

    def test_estimate_cost_with_pricing_data(self):
        """Test cost estimation for model with pricing data."""
        registry = ModelCapabilityRegistry()

        cost = registry.estimate_cost("gpt-4", input_tokens=1000, output_tokens=500)

        assert cost is not None
        assert cost > 0
        # GPT-4 should be relatively expensive
        assert cost > 0.01

    def test_estimate_cost_local_model(self):
        """Test cost estimation for local model (should be None)."""
        registry = ModelCapabilityRegistry()

        cost = registry.estimate_cost("llama-2-7b-chat", input_tokens=1000, output_tokens=500)

        # Local models have no cost data
        assert cost is None

    def test_estimate_cost_nonexistent_model(self):
        """Test cost estimation for non-existent model."""
        registry = ModelCapabilityRegistry()

        cost = registry.estimate_cost("nonexistent-model", input_tokens=1000, output_tokens=500)

        assert cost is None

    def test_estimate_cost_calculation_accuracy(self):
        """Test that cost calculation is accurate."""
        registry = ModelCapabilityRegistry()

        # Get GPT-3.5 Turbo pricing
        gpt35 = registry.get_capability("gpt-3.5-turbo")

        cost = registry.estimate_cost("gpt-3.5-turbo", input_tokens=1000, output_tokens=500)

        expected_cost = (
            1000 * gpt35.cost_per_input_token +
            500 * gpt35.cost_per_output_token
        )

        assert abs(cost - expected_cost) < 0.000001  # Floating point precision


class TestModelCapabilityRegistryTaskPriorities:
    """Test task type priority management."""

    def test_get_task_type_priorities_structure(self):
        """Test that task type priorities have correct structure."""
        registry = ModelCapabilityRegistry()

        priorities = registry.get_task_type_priorities()

        # Should have entry for each task type
        for task_type in TaskType:
            assert task_type in priorities
            assert isinstance(priorities[task_type], list)

        # Lists should contain model IDs
        code_models = priorities[TaskType.CODE_ANALYSIS]
        assert len(code_models) > 0
        assert all(isinstance(model_id, str) for model_id in code_models)

    def test_get_task_type_priorities_sorted_by_quality(self):
        """Test that task priorities are sorted by quality score."""
        registry = ModelCapabilityRegistry()

        priorities = registry.get_task_type_priorities()
        code_models = priorities[TaskType.CODE_ANALYSIS]

        # Check that quality scores are in descending order
        prev_quality = 1.0
        for model_id in code_models:
            capability = registry.get_capability(model_id)
            assert capability.quality_score <= prev_quality
            prev_quality = capability.quality_score

    def test_get_task_type_priorities_includes_relevant_models(self):
        """Test that task priorities include relevant models."""
        registry = ModelCapabilityRegistry()

        priorities = registry.get_task_type_priorities()

        # Code analysis should include GPT-4 and CodeLlama
        code_models = priorities[TaskType.CODE_ANALYSIS]
        assert "gpt-4" in code_models
        assert "codellama-7b-instruct" in code_models

        # Embeddings should include embedding models
        doc_models = priorities[TaskType.DOCUMENT_ANALYSIS]
        assert "text-embedding-ada-002" in doc_models