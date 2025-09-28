"""
Database schemas for Orchesity IDE OSS
Pydantic schemas for database models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestrationRequestCreate(BaseModel):
    """Schema for creating orchestration requests"""

    prompt: str
    providers: List[str]
    max_tokens: int = 1000
    temperature: float = 0.7
    stream: bool = False
    session_id: Optional[str] = None


class OrchestrationRequestResponse(BaseModel):
    """Schema for orchestration request responses"""

    id: int
    request_id: str
    prompt: str
    providers: List[str]
    max_tokens: int
    temperature: float
    stream: bool
    status: RequestStatus
    created_at: datetime
    updated_at: Optional[datetime]
    session_id: Optional[str]
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    total_response_time: Optional[float]
    tokens_used: Optional[int]

    class Config:
        from_attributes = True


class OrchestrationResultCreate(BaseModel):
    """Schema for creating orchestration results"""

    request_id: str
    provider: str
    model: str
    response: str
    tokens_used: Optional[int]
    response_time: float
    error: Optional[str] = None


class OrchestrationResultResponse(BaseModel):
    """Schema for orchestration result responses"""

    id: int
    request_id: str
    provider: str
    model: str
    response: str
    tokens_used: Optional[int]
    response_time: float
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserSessionCreate(BaseModel):
    """Schema for creating user sessions"""

    session_id: str
    user_id: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserSessionResponse(BaseModel):
    """Schema for user session responses"""

    session_id: str
    user_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    preferences: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True


class WorkflowStepSchema(BaseModel):
    """Schema for workflow steps"""

    id: str
    name: str
    provider: str
    prompt_template: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)


class WorkflowCreate(BaseModel):
    """Schema for creating workflows"""

    workflow_id: str
    name: str
    description: Optional[str] = None
    session_id: Optional[str] = None
    steps: List[WorkflowStepSchema]


class WorkflowResponse(BaseModel):
    """Schema for workflow responses"""

    id: int
    workflow_id: str
    name: str
    description: Optional[str]
    session_id: Optional[str]
    steps: List[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    execution_count: int
    last_executed: Optional[datetime]

    class Config:
        from_attributes = True


class WorkflowExecutionCreate(BaseModel):
    """Schema for creating workflow executions"""

    execution_id: str
    workflow_id: str
    input_data: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution responses"""

    id: int
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_data: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration: Optional[float]
    total_tokens_used: Optional[int]
    total_cost: Optional[float]

    class Config:
        from_attributes = True


class CacheEntryResponse(BaseModel):
    """Schema for cache entry responses"""

    id: int
    cache_key: str
    cache_type: str
    created_at: datetime
    expires_at: datetime
    hit_count: int
    last_accessed: datetime
    content_size: Optional[int]
    content_hash: Optional[str]

    class Config:
        from_attributes = True


class ProviderMetricsResponse(BaseModel):
    """Schema for provider metrics responses"""

    id: int
    provider: str
    model: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    total_tokens_used: int
    estimated_cost: float
    window_start: datetime
    last_updated: datetime
    is_healthy: bool
    last_error: Optional[str]
    consecutive_failures: int

    class Config:
        from_attributes = True


class DatabaseStats(BaseModel):
    """Schema for database statistics"""

    total_requests: int
    active_sessions: int
    total_workflows: int
    cache_hit_rate: float
    average_response_time: float
    provider_health: Dict[str, bool]
