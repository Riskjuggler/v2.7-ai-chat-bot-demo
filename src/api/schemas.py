"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=10000)

    class Config:
        json_schema_extra = {
            "example": {"message": "What is the capital of France?"}
        }


class ChatResponse(BaseModel):
    """Response schema for successful chat completion."""

    response: str
    model: str
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "response": "The capital of France is Paris.",
                "model": "gpt-3.5-turbo",
                "timestamp": "2025-11-09T15:00:00",
            }
        }


class ErrorResponse(BaseModel):
    """Response schema for errors."""

    error: str
    detail: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "LLM service unavailable",
                "detail": "Connection timeout after 30s",
            }
        }


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str
    llm_available: bool

    class Config:
        json_schema_extra = {
            "example": {"status": "healthy", "llm_available": True}
        }
