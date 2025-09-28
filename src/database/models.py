"""
Database models for Orchesity IDE OSS
SQLAlchemy models for orchestration requests, sessions, workflows, and caching
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

Base = declarative_base()


class OrchestrationRequestDB(Base):
    """Database model for orchestration requests"""
    
    __tablename__ = "orchestration_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), unique=True, index=True, nullable=False)
    prompt = Column(Text, nullable=False)
    providers = Column(JSON, nullable=False)  # List of provider names
    max_tokens = Column(Integer, default=1000)
    temperature = Column(Float, default=0.7)
    stream = Column(Boolean, default=False)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    session_id = Column(String(50), ForeignKey("user_sessions.session_id"), nullable=True)
    
    # Results and errors stored as JSON
    results = Column(JSON, default=list)
    errors = Column(JSON, default=list)
    
    # Performance metrics
    total_response_time = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Relationships
    session = relationship("UserSessionDB", back_populates="requests")
    results_detail = relationship("OrchestrationResultDB", back_populates="request")


class OrchestrationResultDB(Base):
    """Database model for individual LLM provider results"""
    
    __tablename__ = "orchestration_results"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), ForeignKey("orchestration_requests.request_id"), nullable=False)
    provider = Column(String(20), nullable=False)
    model = Column(String(50), nullable=False)
    response = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=False)
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("OrchestrationRequestDB", back_populates="results_detail")


class UserSessionDB(Base):
    """Database model for user sessions"""
    
    __tablename__ = "user_sessions"
    
    session_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    preferences = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    requests = relationship("OrchestrationRequestDB", back_populates="session")
    workflows = relationship("WorkflowDB", back_populates="session")


class WorkflowDB(Base):
    """Database model for orchestration workflows"""
    
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    session_id = Column(String(50), ForeignKey("user_sessions.session_id"), nullable=True)
    
    # Workflow definition stored as JSON
    steps = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Execution statistics
    execution_count = Column(Integer, default=0)
    last_executed = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("UserSessionDB", back_populates="workflows")
    executions = relationship("WorkflowExecutionDB", back_populates="workflow")


class WorkflowExecutionDB(Base):
    """Database model for workflow execution history"""
    
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(50), unique=True, index=True, nullable=False)
    workflow_id = Column(String(50), ForeignKey("workflows.workflow_id"), nullable=False)
    
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_data = Column(JSON, nullable=True)
    
    # Performance metrics
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_duration = Column(Float, nullable=True)  # seconds
    total_tokens_used = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)  # estimated cost in USD
    
    # Relationships
    workflow = relationship("WorkflowDB", back_populates="executions")


class CacheEntryDB(Base):
    """Database model for caching metadata (Redis stores actual data)"""
    
    __tablename__ = "cache_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(200), unique=True, index=True, nullable=False)
    cache_type = Column(String(50), nullable=False)  # llm_response, session_data, etc.
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Optional metadata about cached content
    content_size = Column(Integer, nullable=True)  # bytes
    content_hash = Column(String(64), nullable=True)  # SHA256 hash


class ProviderMetricsDB(Base):
    """Database model for LLM provider performance metrics"""
    
    __tablename__ = "provider_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), nullable=False)
    model = Column(String(50), nullable=False)
    
    # Performance metrics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    total_tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    # Time window for metrics
    window_start = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Status tracking
    is_healthy = Column(Boolean, default=True)
    last_error = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0)