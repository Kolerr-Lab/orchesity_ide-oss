"""
Database service for CRUD operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid

from .models import (
    OrchestrationRequestDB,
    OrchestrationResultDB,
    UserSessionDB,
    WorkflowDB,
    WorkflowExecutionDB,
    CacheEntryDB,
    ProviderMetricsDB
)
from .schemas import (
    OrchestrationRequestCreate,
    UserSessionCreate,
    WorkflowCreate,
    WorkflowExecutionCreate
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """Database service for CRUD operations"""
    
    def __init__(self):
        pass
    
    # Orchestration Requests
    async def create_orchestration_request(
        self, 
        session: AsyncSession, 
        request_data: OrchestrationRequestCreate,
        request_id: str
    ) -> OrchestrationRequestDB:
        """Create a new orchestration request"""
        db_request = OrchestrationRequestDB(
            request_id=request_id,
            prompt=request_data.prompt,
            providers=request_data.providers,
            max_tokens=request_data.max_tokens,
            temperature=request_data.temperature,
            stream=request_data.stream,
            session_id=request_data.session_id,
            status="pending"
        )
        
        session.add(db_request)
        await session.commit()
        await session.refresh(db_request)
        
        logger.info(f"Created orchestration request: {request_id}")
        return db_request
    
    async def get_orchestration_request(
        self, 
        session: AsyncSession, 
        request_id: str
    ) -> Optional[OrchestrationRequestDB]:
        """Get orchestration request by ID"""
        result = await session.execute(
            select(OrchestrationRequestDB)
            .options(selectinload(OrchestrationRequestDB.results_detail))
            .where(OrchestrationRequestDB.request_id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def update_orchestration_request_status(
        self,
        session: AsyncSession,
        request_id: str,
        status: str,
        results: Optional[List[Dict[str, Any]]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        total_response_time: Optional[float] = None,
        tokens_used: Optional[int] = None
    ) -> bool:
        """Update orchestration request status and results"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if results is not None:
                update_data["results"] = results
            if errors is not None:
                update_data["errors"] = errors
            if total_response_time is not None:
                update_data["total_response_time"] = total_response_time
            if tokens_used is not None:
                update_data["tokens_used"] = tokens_used
            
            await session.execute(
                update(OrchestrationRequestDB)
                .where(OrchestrationRequestDB.request_id == request_id)
                .values(**update_data)
            )
            await session.commit()
            
            logger.info(f"Updated orchestration request {request_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update orchestration request {request_id}: {e}")
            await session.rollback()
            return False
    
    async def get_recent_requests(
        self,
        session: AsyncSession,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[OrchestrationRequestDB]:
        """Get recent orchestration requests"""
        query = select(OrchestrationRequestDB).order_by(
            OrchestrationRequestDB.created_at.desc()
        ).limit(limit)
        
        if session_id:
            query = query.where(OrchestrationRequestDB.session_id == session_id)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    # Orchestration Results
    async def create_orchestration_result(
        self,
        session: AsyncSession,
        request_id: str,
        provider: str,
        model: str,
        response: str,
        tokens_used: Optional[int],
        response_time: float,
        error: Optional[str] = None
    ) -> OrchestrationResultDB:
        """Create an orchestration result"""
        db_result = OrchestrationResultDB(
            request_id=request_id,
            provider=provider,
            model=model,
            response=response,
            tokens_used=tokens_used,
            response_time=response_time,
            error=error
        )
        
        session.add(db_result)
        await session.commit()
        await session.refresh(db_result)
        
        return db_result
    
    # User Sessions
    async def create_user_session(
        self,
        session: AsyncSession,
        session_data: UserSessionCreate
    ) -> UserSessionDB:
        """Create a new user session"""
        db_session = UserSessionDB(
            session_id=session_data.session_id,
            user_id=session_data.user_id,
            preferences=session_data.preferences
        )
        
        session.add(db_session)
        await session.commit()
        await session.refresh(db_session)
        
        logger.info(f"Created user session: {session_data.session_id}")
        return db_session
    
    async def get_user_session(
        self,
        session: AsyncSession,
        session_id: str
    ) -> Optional[UserSessionDB]:
        """Get user session by ID"""
        result = await session.execute(
            select(UserSessionDB).where(UserSessionDB.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def update_session_activity(
        self,
        session: AsyncSession,
        session_id: str
    ) -> bool:
        """Update session last activity"""
        try:
            await session.execute(
                update(UserSessionDB)
                .where(UserSessionDB.session_id == session_id)
                .values(last_activity=datetime.utcnow())
            )
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            await session.rollback()
            return False
    
    # Workflows
    async def create_workflow(
        self,
        session: AsyncSession,
        workflow_data: WorkflowCreate
    ) -> WorkflowDB:
        """Create a new workflow"""
        db_workflow = WorkflowDB(
            workflow_id=workflow_data.workflow_id,
            name=workflow_data.name,
            description=workflow_data.description,
            session_id=workflow_data.session_id,
            steps=[step.dict() for step in workflow_data.steps]
        )
        
        session.add(db_workflow)
        await session.commit()
        await session.refresh(db_workflow)
        
        logger.info(f"Created workflow: {workflow_data.workflow_id}")
        return db_workflow
    
    async def get_workflow(
        self,
        session: AsyncSession,
        workflow_id: str
    ) -> Optional[WorkflowDB]:
        """Get workflow by ID"""
        result = await session.execute(
            select(WorkflowDB)
            .options(selectinload(WorkflowDB.executions))
            .where(WorkflowDB.workflow_id == workflow_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_workflows(
        self,
        session: AsyncSession,
        session_id: str,
        limit: int = 20
    ) -> List[WorkflowDB]:
        """Get workflows for a user session"""
        result = await session.execute(
            select(WorkflowDB)
            .where(WorkflowDB.session_id == session_id)
            .where(WorkflowDB.is_active == True)
            .order_by(WorkflowDB.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    # Provider Metrics
    async def update_provider_metrics(
        self,
        session: AsyncSession,
        provider: str,
        model: str,
        success: bool,
        response_time: float,
        tokens_used: Optional[int] = None,
        estimated_cost: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Update provider performance metrics"""
        # Get or create metrics record
        result = await session.execute(
            select(ProviderMetricsDB)
            .where(ProviderMetricsDB.provider == provider)
            .where(ProviderMetricsDB.model == model)
        )
        
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            metrics = ProviderMetricsDB(
                provider=provider,
                model=model
            )
            session.add(metrics)
        
        # Update metrics
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
            metrics.consecutive_failures = 0
        else:
            metrics.failed_requests += 1
            metrics.consecutive_failures += 1
        
        # Update averages
        total_requests = metrics.total_requests
        current_avg_time = metrics.average_response_time
        metrics.average_response_time = (
            (current_avg_time * (total_requests - 1) + response_time) / total_requests
        )
        
        if tokens_used:
            metrics.total_tokens_used += tokens_used
        if estimated_cost:
            metrics.estimated_cost += estimated_cost
        
        metrics.is_healthy = metrics.consecutive_failures < 5
        if error:
            metrics.last_error = error
        
        metrics.last_updated = datetime.utcnow()
        
        await session.commit()
    
    async def get_provider_metrics(
        self,
        session: AsyncSession
    ) -> List[ProviderMetricsDB]:
        """Get all provider metrics"""
        result = await session.execute(
            select(ProviderMetricsDB).order_by(ProviderMetricsDB.provider)
        )
        return result.scalars().all()
    
    # Database Statistics
    async def get_database_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Count total requests
            total_requests_result = await session.execute(
                select(OrchestrationRequestDB.id).count()
            )
            total_requests = total_requests_result.scalar()
            
            # Count active sessions
            active_sessions_result = await session.execute(
                select(UserSessionDB.session_id)
                .where(UserSessionDB.is_active == True)
                .count()
            )
            active_sessions = active_sessions_result.scalar()
            
            # Count workflows
            total_workflows_result = await session.execute(
                select(WorkflowDB.id).where(WorkflowDB.is_active == True).count()
            )
            total_workflows = total_workflows_result.scalar()
            
            return {
                "total_requests": total_requests or 0,
                "active_sessions": active_sessions or 0,
                "total_workflows": total_workflows or 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global database service instance
db_service = DatabaseService()