"""
Database and cache management router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from ..database.database import get_async_session
from ..database.schemas import (
    OrchestrationRequestResponse,
    UserSessionResponse,
    WorkflowResponse,
    DatabaseStats
)
from ..services.database import db_service
from ..services.cache import cache
from ..utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(session: AsyncSession = Depends(get_async_session)):
    """Get database statistics"""
    try:
        stats = await db_service.get_database_stats(session)
        
        # Add cache stats
        cache_stats = await cache.get_cache_stats()
        
        # Calculate cache hit rate if available
        cache_hit_rate = 0.0
        if cache_stats.get("keyspace_hits", 0) + cache_stats.get("keyspace_misses", 0) > 0:
            total_requests = cache_stats["keyspace_hits"] + cache_stats["keyspace_misses"]
            cache_hit_rate = cache_stats["keyspace_hits"] / total_requests
        
        return DatabaseStats(
            total_requests=stats["total_requests"],
            active_sessions=stats["active_sessions"],
            total_workflows=stats["total_workflows"],
            cache_hit_rate=cache_hit_rate,
            average_response_time=0.0,  # TODO: Calculate from metrics
            provider_health={}  # TODO: Get from provider metrics
        )
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    try:
        return await cache.get_cache_stats()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_cache():
    """Clear all cache data"""
    try:
        cleared_count = await cache.clear_pattern("*")
        return {
            "message": f"Cleared {cleared_count} cache entries",
            "cleared_count": cleared_count
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear/{pattern}")
async def clear_cache_pattern(pattern: str):
    """Clear cache entries matching pattern"""
    try:
        cleared_count = await cache.clear_pattern(pattern)
        return {
            "message": f"Cleared {cleared_count} cache entries matching '{pattern}'",
            "pattern": pattern,
            "cleared_count": cleared_count
        }
    except Exception as e:
        logger.error(f"Failed to clear cache pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/recent", response_model=List[OrchestrationRequestResponse])
async def get_recent_requests(
    limit: int = 50,
    session_id: str = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Get recent orchestration requests"""
    try:
        requests = await db_service.get_recent_requests(session, session_id, limit)
        return requests
    except Exception as e:
        logger.error(f"Failed to get recent requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/active", response_model=List[UserSessionResponse])
async def get_active_sessions(
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    """Get active user sessions"""
    try:
        # TODO: Implement in database service
        return []
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/provider-metrics")
async def get_provider_metrics(session: AsyncSession = Depends(get_async_session)):
    """Get LLM provider performance metrics"""
    try:
        metrics = await db_service.get_provider_metrics(session)
        return [
            {
                "provider": metric.provider,
                "model": metric.model,
                "total_requests": metric.total_requests,
                "success_rate": (
                    metric.successful_requests / metric.total_requests 
                    if metric.total_requests > 0 else 0
                ),
                "average_response_time": metric.average_response_time,
                "total_tokens_used": metric.total_tokens_used,
                "estimated_cost": metric.estimated_cost,
                "is_healthy": metric.is_healthy,
                "consecutive_failures": metric.consecutive_failures,
                "last_updated": metric.last_updated.isoformat()
            }
            for metric in metrics
        ]
    except Exception as e:
        logger.error(f"Failed to get provider metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))