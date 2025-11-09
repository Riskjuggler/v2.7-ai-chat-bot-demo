"""Model capability definitions and routing configuration."""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from ..models.request_models import TaskType


class ModelCategory(str, Enum):
    """Model categories for capability grouping."""
    GENERAL_PURPOSE = "general_purpose"
    CODE_SPECIALIZED = "code_specialized"
    EMBEDDING = "embedding"
    CHAT_OPTIMIZED = "chat_optimized"
    REASONING = "reasoning"
    CREATIVE = "creative"
    SCIENTIFIC = "scientific"
    LOCAL = "local"


@dataclass
class ModelCapability:
    """Model capability information."""
    model_id: str
    provider: str
    category: ModelCategory
    supported_tasks: Set[TaskType]
    context_length: int
    cost_per_input_token: Optional[float] = None
    cost_per_output_token: Optional[float] = None
    quality_score: float = 1.0
    speed_score: float = 1.0
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    max_output_tokens: Optional[int] = None
    description: str = ""


class ModelCapabilityRegistry:
    """Registry of model capabilities for routing decisions."""

    def __init__(self):
        """Initialize the capability registry."""
        self._capabilities: Dict[str, ModelCapability] = {}
        self._initialize_default_capabilities()

    def _initialize_default_capabilities(self):
        """Initialize default model capabilities."""

        # OpenAI Models
        self.register_capability(ModelCapability(
            model_id="gpt-4",
            provider="openai",
            category=ModelCategory.GENERAL_PURPOSE,
            supported_tasks={
                TaskType.GENERAL,
                TaskType.CODE_ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.CODE_REVIEW,
                TaskType.DOCUMENT_ANALYSIS,
                TaskType.DOCUMENT_SUMMARY,
                TaskType.TECHNICAL_WRITING,
                TaskType.DATA_ANALYSIS,
                TaskType.CREATIVE_WRITING,
                TaskType.MATH_REASONING,
                TaskType.SCIENTIFIC_ANALYSIS,
                TaskType.WORKFLOW_PLANNING
            },
            context_length=128000,
            cost_per_input_token=0.00003,
            cost_per_output_token=0.00006,
            quality_score=0.95,
            speed_score=0.7,
            supports_functions=True,
            max_output_tokens=4096,
            description="Most capable GPT-4 model for complex tasks"
        ))

        self.register_capability(ModelCapability(
            model_id="gpt-4-turbo",
            provider="openai",
            category=ModelCategory.GENERAL_PURPOSE,
            supported_tasks={
                TaskType.GENERAL,
                TaskType.CODE_ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.CODE_REVIEW,
                TaskType.DOCUMENT_ANALYSIS,
                TaskType.DOCUMENT_SUMMARY,
                TaskType.TECHNICAL_WRITING,
                TaskType.DATA_ANALYSIS,
                TaskType.CREATIVE_WRITING,
                TaskType.MATH_REASONING,
                TaskType.SCIENTIFIC_ANALYSIS,
                TaskType.WORKFLOW_PLANNING
            },
            context_length=128000,
            cost_per_input_token=0.00001,
            cost_per_output_token=0.00003,
            quality_score=0.92,
            speed_score=0.85,
            supports_functions=True,
            supports_vision=True,
            max_output_tokens=4096,
            description="Fast and capable GPT-4 variant"
        ))

        self.register_capability(ModelCapability(
            model_id="gpt-3.5-turbo",
            provider="openai",
            category=ModelCategory.CHAT_OPTIMIZED,
            supported_tasks={
                TaskType.GENERAL,
                TaskType.CODE_GENERATION,
                TaskType.DOCUMENT_SUMMARY,
                TaskType.CREATIVE_WRITING,
                TaskType.TRANSLATION
            },
            context_length=16385,
            cost_per_input_token=0.0000015,
            cost_per_output_token=0.000002,
            quality_score=0.8,
            speed_score=0.95,
            supports_functions=True,
            max_output_tokens=4096,
            description="Fast and cost-effective for simpler tasks"
        ))

        self.register_capability(ModelCapability(
            model_id="text-embedding-ada-002",
            provider="openai",
            category=ModelCategory.EMBEDDING,
            supported_tasks={TaskType.DOCUMENT_ANALYSIS},
            context_length=8191,
            cost_per_input_token=0.0000001,
            quality_score=0.85,
            speed_score=0.9,
            supports_streaming=False,
            description="High-quality text embeddings"
        ))

        # Anthropic Models
        self.register_capability(ModelCapability(
            model_id="claude-3-opus-20240229",
            provider="anthropic",
            category=ModelCategory.REASONING,
            supported_tasks={
                TaskType.GENERAL,
                TaskType.CODE_ANALYSIS,
                TaskType.CODE_REVIEW,
                TaskType.DOCUMENT_ANALYSIS,
                TaskType.TECHNICAL_WRITING,
                TaskType.DATA_ANALYSIS,
                TaskType.MATH_REASONING,
                TaskType.SCIENTIFIC_ANALYSIS,
                TaskType.WORKFLOW_PLANNING
            },
            context_length=200000,
            cost_per_input_token=0.000015,
            cost_per_output_token=0.000075,
            quality_score=0.98,
            speed_score=0.6,
            supports_vision=True,
            max_output_tokens=4096,
            description="Most capable Claude model for complex reasoning"
        ))

        self.register_capability(ModelCapability(
            model_id="claude-3-sonnet-20240229",
            provider="anthropic",
            category=ModelCategory.GENERAL_PURPOSE,
            supported_tasks={
                TaskType.GENERAL,
                TaskType.CODE_ANALYSIS,
                TaskType.CODE_GENERATION,
                TaskType.DOCUMENT_ANALYSIS,
                TaskType.DOCUMENT_SUMMARY,
                TaskType.TECHNICAL_WRITING,
                TaskType.CREATIVE_WRITING,
                TaskType.TRANSLATION
            },
            context_length=200000,
            cost_per_input_token=0.000003,
            cost_per_output_token=0.000015,
            quality_score=0.9,
            speed_score=0.8,
            supports_vision=True,
            max_output_tokens=4096,
            description="Balanced Claude model for most tasks"
        ))

        self.register_capability(ModelCapability(
            model_id="claude-3-haiku-20240307",
            provider="anthropic",
            category=ModelCategory.CHAT_OPTIMIZED,
            supported_tasks={
                TaskType.GENERAL,
                TaskType.DOCUMENT_SUMMARY,
                TaskType.CREATIVE_WRITING,
                TaskType.TRANSLATION
            },
            context_length=200000,
            cost_per_input_token=0.00000025,
            cost_per_output_token=0.00000125,
            quality_score=0.8,
            speed_score=0.95,
            supports_vision=True,
            max_output_tokens=4096,
            description="Fast and cost-effective Claude model"
        ))

        # Local Models (LMStudio)
        # NOTE: LMStudio models are now dynamically discovered and registered at runtime
        # Static registration disabled to prevent routing to non-existent models
        # See LLMService._register_provider_models() for dynamic registration

        # self.register_capability(ModelCapability(
        #     model_id="llama-2-7b-chat",
        #     provider="lmstudio",
        #     category=ModelCategory.LOCAL,
        #     supported_tasks={
        #         TaskType.GENERAL,
        #         TaskType.CREATIVE_WRITING,
        #         TaskType.TRANSLATION
        #     },
        #     context_length=4096,
        #     quality_score=0.7,
        #     speed_score=0.8,
        #     supports_functions=False,
        #     max_output_tokens=2048,
        #     description="Local Llama 2 7B chat model"
        # ))

        # self.register_capability(ModelCapability(
        #     model_id="llama-2-13b-chat",
        #     provider="lmstudio",
        #     category=ModelCategory.LOCAL,
        #     supported_tasks={
        #         TaskType.GENERAL,
        #         TaskType.CODE_GENERATION,
        #         TaskType.DOCUMENT_SUMMARY,
        #         TaskType.CREATIVE_WRITING,
        #         TaskType.TRANSLATION
        #     },
        #     context_length=4096,
        #     quality_score=0.75,
        #     speed_score=0.6,
        #     supports_functions=False,
        #     max_output_tokens=2048,
        #     description="Local Llama 2 13B chat model"
        # ))

        # self.register_capability(ModelCapability(
        #     model_id="codellama-7b-instruct",
        #     provider="lmstudio",
        #     category=ModelCategory.CODE_SPECIALIZED,
        #     supported_tasks={
        #         TaskType.CODE_ANALYSIS,
        #         TaskType.CODE_GENERATION,
        #         TaskType.CODE_REVIEW
        #     },
        #     context_length=4096,
        #     quality_score=0.8,
        #     speed_score=0.8,
        #     supports_functions=False,
        #     max_output_tokens=2048,
        #     description="Local CodeLlama 7B for code tasks"
        # ))

        # self.register_capability(ModelCapability(
        #     model_id="codellama-13b-instruct",
        #     provider="lmstudio",
        #     category=ModelCategory.CODE_SPECIALIZED,
        #     supported_tasks={
        #         TaskType.CODE_ANALYSIS,
        #         TaskType.CODE_GENERATION,
        #         TaskType.CODE_REVIEW,
        #         TaskType.TECHNICAL_WRITING
        #     },
        #     context_length=4096,
        #     quality_score=0.85,
        #     speed_score=0.6,
        #     supports_functions=False,
        #     max_output_tokens=2048,
        #     description="Local CodeLlama 13B for complex code tasks"
        # ))

    def register_capability(self, capability: ModelCapability):
        """Register a model capability.

        Args:
            capability: Model capability to register
        """
        self._capabilities[capability.model_id] = capability

    def get_capability(self, model_id: str) -> Optional[ModelCapability]:
        """Get capability for a model.

        Args:
            model_id: Model identifier

        Returns:
            Model capability or None if not found
        """
        return self._capabilities.get(model_id)

    def get_models_for_task(self, task_type: TaskType) -> List[ModelCapability]:
        """Get models that support a specific task.

        Args:
            task_type: Task type to filter by

        Returns:
            List of supporting models
        """
        return [
            capability for capability in self._capabilities.values()
            if task_type in capability.supported_tasks
        ]

    def get_models_by_provider(self, provider: str) -> List[ModelCapability]:
        """Get models from a specific provider.

        Args:
            provider: Provider name

        Returns:
            List of models from provider
        """
        return [
            capability for capability in self._capabilities.values()
            if capability.provider == provider
        ]

    def get_models_by_category(self, category: ModelCategory) -> List[ModelCapability]:
        """Get models in a specific category.

        Args:
            category: Model category

        Returns:
            List of models in category
        """
        return [
            capability for capability in self._capabilities.values()
            if capability.category == category
        ]

    def get_best_model_for_task(
        self,
        task_type: TaskType,
        prefer_local: bool = False,
        max_cost_per_token: Optional[float] = None,
        min_quality_score: float = 0.0,
        min_speed_score: float = 0.0,
        required_context_length: Optional[int] = None
    ) -> Optional[ModelCapability]:
        """Get the best model for a specific task based on criteria.

        Args:
            task_type: Task type
            prefer_local: Prefer local models
            max_cost_per_token: Maximum cost per token
            min_quality_score: Minimum quality score
            min_speed_score: Minimum speed score
            required_context_length: Required context length

        Returns:
            Best matching model capability
        """
        candidates = self.get_models_for_task(task_type)

        # Apply filters
        filtered_candidates = []
        for candidate in candidates:
            # Quality filter
            if candidate.quality_score < min_quality_score:
                continue

            # Speed filter
            if candidate.speed_score < min_speed_score:
                continue

            # Cost filter
            if (max_cost_per_token is not None and
                candidate.cost_per_output_token is not None and
                candidate.cost_per_output_token > max_cost_per_token):
                continue

            # Context length filter
            if (required_context_length is not None and
                candidate.context_length < required_context_length):
                continue

            filtered_candidates.append(candidate)

        if not filtered_candidates:
            return None

        # Sort by preference
        if prefer_local:
            # Prefer local models, then by quality
            filtered_candidates.sort(
                key=lambda x: (
                    0 if x.category == ModelCategory.LOCAL else 1,
                    -x.quality_score
                )
            )
        else:
            # Sort by quality, then cost-effectiveness
            filtered_candidates.sort(
                key=lambda x: (
                    -x.quality_score,
                    x.cost_per_output_token or 0
                )
            )

        return filtered_candidates[0]

    def get_all_capabilities(self) -> Dict[str, ModelCapability]:
        """Get all registered capabilities.

        Returns:
            Dictionary of all capabilities
        """
        return self._capabilities.copy()

    def get_task_type_priorities(self) -> Dict[TaskType, List[str]]:
        """Get prioritized model lists for each task type.

        Returns:
            Dictionary mapping task types to prioritized model lists
        """
        priorities = {}

        for task_type in TaskType:
            models = self.get_models_for_task(task_type)
            # Sort by quality score descending
            models.sort(key=lambda x: -x.quality_score)
            priorities[task_type] = [model.model_id for model in models]

        return priorities

    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> Optional[float]:
        """Estimate cost for a request.

        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD, None if cost data unavailable
        """
        capability = self.get_capability(model_id)
        if not capability:
            return None

        cost = 0.0
        if capability.cost_per_input_token:
            cost += input_tokens * capability.cost_per_input_token
        if capability.cost_per_output_token:
            cost += output_tokens * capability.cost_per_output_token

        return cost if (capability.cost_per_input_token or capability.cost_per_output_token) else None