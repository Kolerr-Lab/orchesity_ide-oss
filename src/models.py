"""
Pydantic models for Orchesity IDE OSS
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROK = "grok"


class OrchestrationRequest(BaseModel):
    """Request model for LLM orchestration"""

    prompt: str = Field(..., description="The prompt to send to LLMs")
    providers: List[LLMProvider] = Field(
        default_factory=lambda: [LLMProvider.OPENAI],
        description="List of LLM providers to use",
    )
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(
        0.7, description="Creativity temperature (0-1)"
    )
    stream: bool = Field(False, description="Whether to stream the response")


class OrchestrationResponse(BaseModel):
    """Response model for LLM orchestration"""

    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Request status")
    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Results from each LLM provider"
    )
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Any errors that occurred"
    )


class LLMResult(BaseModel):
    """Result from a single LLM provider"""

    provider: LLMProvider
    model: str
    response: str
    tokens_used: Optional[int] = None
    response_time: float
    error: Optional[str] = None


class UserSession(BaseModel):
    """User session model"""

    session_id: str
    user_id: Optional[str] = None
    created_at: str
    last_activity: str
    preferences: Dict[str, Any] = Field(default_factory=dict)


class HealthStatus(BaseModel):
    """Health check status"""

    status: str  # "healthy" or "unhealthy"
    timestamp: str
    version: str
    services: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    """Step in an orchestration workflow"""

    id: str
    name: str
    provider: LLMProvider
    prompt_template: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)  # IDs of prerequisite steps


class Workflow(BaseModel):
    """Complete orchestration workflow"""

    id: str
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]
    created_at: str
    updated_at: str
