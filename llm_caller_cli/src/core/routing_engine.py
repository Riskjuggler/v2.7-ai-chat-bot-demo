"""Model capability routing engine for intelligent model selection."""

import re
from typing import Dict, List, Optional, Tuple, Any
from ..models.request_models import (
    TaskType,
    ChatCompletionRequest,
    CompletionRequest,
    EmbeddingRequest,
    RoutingDecision
)
from ..config.model_capabilities import ModelCapabilityRegistry, ModelCapability


class RoutingEngine:
    """Intelligent routing engine for model selection based on task requirements."""

    def __init__(self, capability_registry: Optional[ModelCapabilityRegistry] = None):
        """Initialize the routing engine.

        Args:
            capability_registry: Model capability registry
        """
        self.capability_registry = capability_registry or ModelCapabilityRegistry()
        self._task_detection_patterns = self._initialize_task_patterns()

    def _initialize_task_patterns(self) -> Dict[TaskType, List[str]]:
        """Initialize task detection patterns.

        Returns:
            Dictionary mapping task types to detection patterns
        """
        return {
            TaskType.CODE_ANALYSIS: [
                r"\b(?:analyze|explain|understand)\b.*\b(?:code|function|method|class|algorithm|implementation)",
                r"\bexplain\b.*\b(?:what|how)\b.*\b(?:code|function|method|algorithm)",
                r"what does (?:this|the) (?:code|function|method|class|algorithm|implementation) do",
                r"explain (?:this|the) (?:code|function|method|algorithm|implementation)",
                r"analyze (?:this|the) (?:code|function|method|algorithm|implementation)",
                r"understand (?:this|the) (?:code|function|method|algorithm|implementation)",
                r"review (?:this|the) (?:implementation|algorithm) of"
            ],
            TaskType.CODE_GENERATION: [
                r"\b(?:write|create|generate|implement|build|make)\b.*\b(?:function|method|class|script|program|code|algorithm)",
                r"write (?:a|an|the)? (?:function|method|class|script|program|code)",
                r"create (?:a|an|the)? (?:function|method|class|script|program|code)",
                r"implement (?:a|an|the)? (?:function|method|class|algorithm|code)",
                r"generate (?:code|a function|a method|a class|a program)",
                r"build (?:a|an|the)? (?:function|method|class|script|program|code)",
                r"make a (?:function|method|class|script|program) (?:to|that|for)"
            ],
            TaskType.CODE_REVIEW: [
                r"\b(?:check|audit|validate|critique)\b.*\b(?:code|implementation|pull request|PR)\b",
                r"code review",
                r"review (?:this|the|my) code\b(?! of)",
                r"review (?:the|my) pull request",
                r"check (?:this|the|my) (?:code|implementation)",
                r"find (?:bugs|issues|problems) in (?:this|the) code"
            ],
            TaskType.DOCUMENT_ANALYSIS: [
                r"\b(?:analyze|examine|study|review)\b.*\b(?:document|text|content|paper|article)\b",
                r"\b(?:document|text|content)\b.*\b(?:analysis|examination|review)\b",
                r"analyze (?:this|the) (?:document|text|content|paper)",
                r"what (?:is|does) (?:this|the) (?:document|text|paper) (?:about|say|contain)",
                r"extract (?:information|data|insights) from (?:this|the) (?:document|text)"
            ],
            TaskType.DOCUMENT_SUMMARY: [
                r"\b(?:summarize|summarise|sum up)\b.*\b(?:document|text|content|article|paper)\b",
                r"\b(?:summary|overview|synopsis)\b.*\b(?:of|for)\b.*\b(?:document|text|article)\b",
                r"summarize (?:this|the) (?:document|text|content|article|paper)",
                r"give me a summary of (?:this|the) (?:document|text|article)",
                r"what are the key points of (?:this|the) (?:document|text|article)"
            ],
            TaskType.TECHNICAL_WRITING: [
                r"\b(?:write|create|draft|compose)\b.*\b(?:documentation|manual|guide|specification|README)\b",
                r"\b(?:documentation|manual|guide|specification|README)\b.*\b(?:for|about)\b",
                r"write (?:documentation|a manual|a guide|a specification)",
                r"create (?:documentation|a manual|a guide|a specification)",
                r"document (?:this|the) (?:code|function|API|system)"
            ],
            TaskType.DATA_ANALYSIS: [
                r"\b(?:analyze|examine|study|interpret)\b.*\b(?:data|dataset|statistics|metrics|numbers)\b",
                r"\b(?:data|dataset|statistics|metrics)\b.*\b(?:analysis|examination|interpretation)\b",
                r"analyze (?:this|the) (?:data|dataset|statistics|metrics)",
                r"what (?:does|do) (?:this|the) (?:data|statistics|numbers) (?:show|tell|mean)",
                r"interpret (?:this|the) (?:data|results|statistics)"
            ],
            TaskType.CREATIVE_WRITING: [
                r"\b(?:write|create|compose)\b.*\b(?:story|poem|creative|fiction|narrative|novel|script)\b",
                r"\b(?:creative|fiction|story|poem|narrative)\b.*\b(?:writing|content)\b",
                r"write a (?:story|poem|creative piece|fiction|narrative)",
                r"create a (?:story|poem|creative piece|fiction|narrative)",
                r"compose a (?:story|poem|creative piece|fiction)"
            ],
            TaskType.TRANSLATION: [
                r"\b(?:translate|translation)\b",
                r"translate (?:this|the) (?:text|document|content)",
                r"(?:from|to) (?:english|spanish|french|german|chinese|japanese|korean|italian|portuguese|russian)",
                r"in (?:english|spanish|french|german|chinese|japanese|korean|italian|portuguese|russian)"
            ],
            TaskType.MATH_REASONING: [
                r"\b(?:solve|calculate|compute|math|mathematical|equation|formula|algebra|calculus|geometry)\b",
                r"solve (?:this|the) (?:problem|equation|math)",
                r"calculate (?:this|the) (?:value|result|answer)",
                r"what (?:is|equals) (?:\d+|\w+) (?:\+|\-|\*|\/|[\^]) (?:\d+|\w+)",
                r"mathematical (?:problem|equation|calculation)"
            ],
            TaskType.SCIENTIFIC_ANALYSIS: [
                r"\b(?:scientific|research|study|experiment|hypothesis|theory|analysis)\b",
                r"scientific (?:analysis|research|study|method)",
                r"research (?:paper|study|analysis|question)",
                r"analyze (?:this|the) (?:research|study|experiment|data|results)"
            ],
            TaskType.WORKFLOW_PLANNING: [
                r"\b(?:plan|planning|workflow|process|strategy|steps|procedure)\b",
                r"plan (?:a|the) (?:workflow|process|strategy|project)",
                r"what (?:steps|process|workflow) (?:should|do) (?:I|we)",
                r"how (?:should|do) (?:I|we) (?:approach|tackle|handle|plan)",
                r"create a (?:plan|workflow|process|strategy)"
            ]
        }

    def detect_task_type(self, text: str) -> TaskType:
        """Detect task type from input text.

        Args:
            text: Input text to analyze

        Returns:
            Detected task type
        """
        text_lower = text.lower()

        # Define priority order for task types (higher priority first)
        priority_order = [
            TaskType.CODE_GENERATION,
            TaskType.CODE_ANALYSIS,
            TaskType.CODE_REVIEW,
            TaskType.TECHNICAL_WRITING,
            TaskType.DOCUMENT_SUMMARY,
            TaskType.DOCUMENT_ANALYSIS,
            TaskType.CREATIVE_WRITING,
            TaskType.TRANSLATION,
            TaskType.MATH_REASONING,
            TaskType.SCIENTIFIC_ANALYSIS,
            TaskType.DATA_ANALYSIS,
            TaskType.WORKFLOW_PLANNING
        ]

        # Score each task type based on pattern matches
        task_scores = {}
        for task_type in priority_order:
            if task_type in self._task_detection_patterns:
                patterns = self._task_detection_patterns[task_type]
                score = 0
                for pattern in patterns:
                    matches = re.findall(pattern, text_lower)
                    score += len(matches)
                if score > 0:
                    task_scores[task_type] = score

        # Return the highest scoring task type (with priority order as tiebreaker)
        if task_scores:
            # Sort by score descending, then by priority order
            sorted_tasks = sorted(
                task_scores.items(),
                key=lambda x: (x[1], -priority_order.index(x[0])),
                reverse=True
            )
            return sorted_tasks[0][0]

        # Default to general if no specific task detected
        return TaskType.GENERAL

    def route_chat_completion(
        self,
        request: ChatCompletionRequest,
        available_providers: List[str]
    ) -> RoutingDecision:
        """Route chat completion request to best model.

        Args:
            request: Chat completion request
            available_providers: List of available provider names

        Returns:
            Routing decision with selected model and reasoning
        """
        # If model is explicitly specified, validate and use it
        if request.model:
            capability = self.capability_registry.get_capability(request.model)
            if capability and capability.provider in available_providers:
                return RoutingDecision(
                    selected_model=request.model,
                    selected_provider=capability.provider,
                    reasoning=f"User explicitly requested model: {request.model}",
                    task_type=request.task_type or TaskType.GENERAL,
                    confidence_score=1.0
                )

        # Detect task type if not provided
        task_type = request.task_type
        if not task_type:
            # Combine all message content for task detection
            combined_text = " ".join([msg.content for msg in request.messages])
            task_type = self.detect_task_type(combined_text)

        # Calculate context requirements
        total_tokens = sum(
            self._estimate_tokens(msg.content) for msg in request.messages
        )
        required_context = total_tokens + (request.max_tokens or 1000)

        # Find best model for task
        best_model = self.capability_registry.get_best_model_for_task(
            task_type=task_type,
            prefer_local=request.prefer_local,
            required_context_length=required_context
        )

        if not best_model or best_model.provider not in available_providers:
            # Fallback to available models
            best_model = self._find_fallback_model(
                task_type, available_providers, required_context
            )

        if not best_model:
            # Last resort: any available model
            all_capabilities = self.capability_registry.get_all_capabilities()
            for capability in all_capabilities.values():
                if capability.provider in available_providers:
                    best_model = capability
                    break

        if not best_model:
            raise ValueError("No suitable model found for request")

        # Build fallback list
        fallback_models = self._get_fallback_models(
            task_type, available_providers, best_model.model_id
        )

        reasoning = self._build_routing_reasoning(
            task_type, best_model, request.prefer_local, required_context
        )

        return RoutingDecision(
            selected_model=best_model.model_id,
            selected_provider=best_model.provider,
            reasoning=reasoning,
            task_type=task_type,
            confidence_score=self._calculate_confidence_score(best_model, task_type),
            fallback_models=fallback_models
        )

    def route_completion(
        self,
        request: CompletionRequest,
        available_providers: List[str]
    ) -> RoutingDecision:
        """Route completion request to best model.

        Args:
            request: Completion request
            available_providers: List of available provider names

        Returns:
            Routing decision with selected model and reasoning
        """
        # Similar logic to chat completion
        if request.model:
            capability = self.capability_registry.get_capability(request.model)
            if capability and capability.provider in available_providers:
                return RoutingDecision(
                    selected_model=request.model,
                    selected_provider=capability.provider,
                    reasoning=f"User explicitly requested model: {request.model}",
                    task_type=request.task_type or TaskType.GENERAL,
                    confidence_score=1.0
                )

        task_type = request.task_type or self.detect_task_type(request.prompt)
        required_context = self._estimate_tokens(request.prompt) + (request.max_tokens or 1000)

        best_model = self.capability_registry.get_best_model_for_task(
            task_type=task_type,
            prefer_local=request.prefer_local,
            required_context_length=required_context
        )

        if not best_model or best_model.provider not in available_providers:
            best_model = self._find_fallback_model(
                task_type, available_providers, required_context
            )

        if not best_model:
            raise ValueError("No suitable model found for request")

        fallback_models = self._get_fallback_models(
            task_type, available_providers, best_model.model_id
        )

        reasoning = self._build_routing_reasoning(
            task_type, best_model, request.prefer_local, required_context
        )

        return RoutingDecision(
            selected_model=best_model.model_id,
            selected_provider=best_model.provider,
            reasoning=reasoning,
            task_type=task_type,
            confidence_score=self._calculate_confidence_score(best_model, task_type),
            fallback_models=fallback_models
        )

    def route_embedding(
        self,
        request: EmbeddingRequest,
        available_providers: List[str]
    ) -> RoutingDecision:
        """Route embedding request to best model.

        Args:
            request: Embedding request
            available_providers: List of available provider names

        Returns:
            Routing decision with selected model and reasoning
        """
        if request.model:
            capability = self.capability_registry.get_capability(request.model)
            if capability and capability.provider in available_providers:
                return RoutingDecision(
                    selected_model=request.model,
                    selected_provider=capability.provider,
                    reasoning=f"User explicitly requested embedding model: {request.model}",
                    task_type=TaskType.DOCUMENT_ANALYSIS,
                    confidence_score=1.0
                )

        # Find best embedding model
        embedding_models = [
            cap for cap in self.capability_registry.get_all_capabilities().values()
            if cap.category.value == "embedding" and cap.provider in available_providers
        ]

        if not embedding_models:
            raise ValueError("No embedding models available")

        # Sort by quality score
        embedding_models.sort(key=lambda x: -x.quality_score)
        best_model = embedding_models[0]

        return RoutingDecision(
            selected_model=best_model.model_id,
            selected_provider=best_model.provider,
            reasoning=f"Selected best available embedding model: {best_model.model_id}",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            confidence_score=0.9,
            fallback_models=[m.model_id for m in embedding_models[1:3]]
        )

    def _find_fallback_model(
        self,
        task_type: TaskType,
        available_providers: List[str],
        required_context: int
    ) -> Optional[ModelCapability]:
        """Find fallback model when primary selection fails.

        Args:
            task_type: Task type
            available_providers: Available provider names
            required_context: Required context length

        Returns:
            Fallback model capability or None
        """
        all_capabilities = self.capability_registry.get_all_capabilities()
        candidates = [
            cap for cap in all_capabilities.values()
            if (cap.provider in available_providers and
                cap.context_length >= required_context)
        ]

        if not candidates:
            # Relax context requirement
            candidates = [
                cap for cap in all_capabilities.values()
                if cap.provider in available_providers
            ]

        if not candidates:
            return None

        # Sort by quality score
        candidates.sort(key=lambda x: -x.quality_score)
        return candidates[0]

    def _get_fallback_models(
        self,
        task_type: TaskType,
        available_providers: List[str],
        exclude_model: str
    ) -> List[str]:
        """Get fallback models for a task.

        Args:
            task_type: Task type
            available_providers: Available provider names
            exclude_model: Model to exclude from fallbacks

        Returns:
            List of fallback model IDs
        """
        models = self.capability_registry.get_models_for_task(task_type)
        fallbacks = [
            model.model_id for model in models
            if (model.provider in available_providers and
                model.model_id != exclude_model)
        ]
        return fallbacks[:3]  # Return top 3 fallbacks

    def _build_routing_reasoning(
        self,
        task_type: TaskType,
        selected_model: ModelCapability,
        prefer_local: bool,
        required_context: int
    ) -> str:
        """Build human-readable routing reasoning.

        Args:
            task_type: Detected/specified task type
            selected_model: Selected model capability
            prefer_local: Whether local models were preferred
            required_context: Required context length

        Returns:
            Routing reasoning explanation
        """
        reasons = []

        if task_type != TaskType.GENERAL:
            reasons.append(f"Task type detected: {task_type.value}")

        reasons.append(
            f"Selected {selected_model.model_id} "
            f"(quality: {selected_model.quality_score:.2f}, "
            f"speed: {selected_model.speed_score:.2f})"
        )

        if prefer_local and selected_model.category.value == "local":
            reasons.append("Preferred local model for privacy")
        elif prefer_local and selected_model.category.value != "local":
            reasons.append("Local model not available, using cloud model")

        if required_context > 4096:
            reasons.append(f"Required large context ({required_context} tokens)")

        return "; ".join(reasons)

    def _calculate_confidence_score(
        self,
        selected_model: ModelCapability,
        task_type: TaskType
    ) -> float:
        """Calculate confidence score for routing decision.

        Args:
            selected_model: Selected model capability
            task_type: Task type

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_score = selected_model.quality_score

        # Boost confidence if model is specialized for task
        if task_type in selected_model.supported_tasks:
            if selected_model.category.value in ["code_specialized", "embedding"]:
                base_score += 0.1  # Specialized models get confidence boost

        return min(1.0, base_score)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters
        return max(1, len(text) // 4)

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics and model utilization data.

        Returns:
            Statistics dictionary
        """
        capabilities = self.capability_registry.get_all_capabilities()

        stats = {
            "total_models": len(capabilities),
            "providers": list(set(cap.provider for cap in capabilities.values())),
            "categories": list(set(cap.category.value for cap in capabilities.values())),
            "models_by_provider": {},
            "models_by_category": {},
            "task_coverage": {}
        }

        # Models by provider
        for provider in stats["providers"]:
            provider_models = self.capability_registry.get_models_by_provider(provider)
            stats["models_by_provider"][provider] = [m.model_id for m in provider_models]

        # Models by category
        for category_str in stats["categories"]:
            from ..config.model_capabilities import ModelCategory
            try:
                category = ModelCategory(category_str)
                category_models = self.capability_registry.get_models_by_category(category)
                stats["models_by_category"][category_str] = [m.model_id for m in category_models]
            except ValueError:
                continue

        # Task coverage
        for task_type in TaskType:
            task_models = self.capability_registry.get_models_for_task(task_type)
            stats["task_coverage"][task_type.value] = {
                "model_count": len(task_models),
                "models": [m.model_id for m in task_models[:5]]  # Top 5
            }

        return stats