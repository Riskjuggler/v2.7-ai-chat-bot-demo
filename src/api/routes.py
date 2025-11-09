"""API route definitions."""

from fastapi import APIRouter, HTTPException
from .schemas import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from .service import LLMService

router = APIRouter()
llm_service = LLMService()


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the LLM and get response.

    Args:
        request: Chat request with message field

    Returns:
        Chat response with LLM's reply

    Raises:
        HTTPException: 503 if LLM timeout, 500 for other errors
    """
    try:
        response_text, model_name, timestamp = await llm_service.chat(request.message)
        return ChatResponse(
            response=response_text, model=model_name, timestamp=timestamp
        )
    except TimeoutError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ConnectionError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Check API and LLM service health.

    Returns:
        Health status with LLM availability
    """
    llm_available = await llm_service.health_check()
    return HealthResponse(status="healthy", llm_available=llm_available)
