"""Request and response models for LLM Caller service."""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum


class TaskType(str, Enum):
    """Supported task types for model routing."""
    GENERAL = "general"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DOCUMENT_ANALYSIS = "document_analysis"
    DOCUMENT_SUMMARY = "document_summary"
    TECHNICAL_WRITING = "technical_writing"
    DATA_ANALYSIS = "data_analysis"
    CREATIVE_WRITING = "creative_writing"
    TRANSLATION = "translation"
    MATH_REASONING = "math_reasoning"
    SCIENTIFIC_ANALYSIS = "scientific_analysis"
    WORKFLOW_PLANNING = "workflow_planning"


class MessageRole(str, Enum):
    """Message roles for chat completions."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatMessage(BaseModel):
    """Chat message for completion requests."""
    role: MessageRole
    content: str
    name: Optional[str] = None


class FunctionCall(BaseModel):
    """Function call specification."""
    name: str
    arguments: str


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions."""
    messages: List[ChatMessage]
    model: Optional[str] = None
    task_type: Optional[TaskType] = None
    prefer_local: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: bool = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, Any]]] = None


class CompletionRequest(BaseModel):
    """Request model for text completions."""
    prompt: str
    model: Optional[str] = None
    task_type: Optional[TaskType] = None
    prefer_local: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: bool = False
    logprobs: Optional[int] = None
    echo: bool = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    best_of: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class EmbeddingRequest(BaseModel):
    """Request model for embeddings."""
    input: Union[str, List[str]]
    model: Optional[str] = None
    user: Optional[str] = None


class Choice(BaseModel):
    """Choice in completion response."""
    index: int
    text: Optional[str] = None
    message: Optional[ChatMessage] = None
    logprobs: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: Optional[int] = None
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response model for chat completions."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    provider: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class CompletionResponse(BaseModel):
    """Response model for text completions."""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    provider: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class EmbeddingData(BaseModel):
    """Embedding data item."""
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    provider: str
    usage: Optional[Usage] = None


class ModelInfo(BaseModel):
    """Information about an available model."""
    id: str
    object: str = "model"
    created: Optional[int] = None
    owned_by: str
    provider: str
    capabilities: List[str] = Field(default_factory=list)
    context_length: Optional[int] = None
    description: Optional[str] = None


class ModelsResponse(BaseModel):
    """Response model for listing models."""
    object: str = "list"
    data: List[ModelInfo]


class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str
    message: str
    param: Optional[str] = None
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: ErrorDetail


class HealthStatus(BaseModel):
    """Health check status."""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: int
    providers: Dict[str, Dict[str, Any]]
    models_available: int
    uptime_seconds: float


class ProviderStatus(BaseModel):
    """Provider-specific status."""
    name: str
    status: Literal["online", "offline", "error"]
    models_available: List[str]
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: int


class MetricsData(BaseModel):
    """Usage metrics data."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency_ms: float
    total_tokens_used: int
    provider_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    task_breakdown: Dict[str, int] = Field(default_factory=dict)
    model_breakdown: Dict[str, int] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Model routing decision."""
    selected_model: str
    selected_provider: str
    reasoning: str
    task_type: TaskType
    confidence_score: float
    fallback_models: List[str] = Field(default_factory=list)


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    provider: str
    choices: List[Dict[str, Any]]


class ConfigValidation(BaseModel):
    """Configuration validation result."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    provider_status: Dict[str, bool] = Field(default_factory=dict)