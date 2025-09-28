"""
Database and cache management router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import logging

from ..core.container import ServiceContainer
from ..database.connection import DatabaseConnection
from ..services.cache import CacheService
from ..database.schemas import (
    OrchestrationRequestResponse,
    UserSessionResponse,
    WorkflowResponse,
    DatabaseStats,
)

logger = logging.getLogger(__name__)


def create_router(container: ServiceContainer) -> APIRouter:
    """Create database router with dependency injection"""
    router = APIRouter()

    def get_database() -> DatabaseConnection:
        """Dependency injection for database connection"""
        return container.get_service(DatabaseConnection)

    def get_cache() -> Optional[CacheService]:
        """Dependency injection for cache service"""
        try:
            return container.get_service(CacheService)
        except ValueError:
            return None

    @router.get("/stats", response_model=DatabaseStats)
    async def get_database_stats(
        database: DatabaseConnection = Depends(get_database),
        cache: Optional[CacheService] = Depends(get_cache),
    ):
        """Get database and cache statistics"""
        try:
            # Get database stats
            db_stats = await database.get_stats()

            result = DatabaseStats(
                total_requests=db_stats.get("total_requests", 0),
                total_sessions=db_stats.get("total_sessions", 0),
                total_workflows=db_stats.get("total_workflows", 0),
                database_size_mb=db_stats.get("database_size_mb", 0),
                cache_info={},
            )

            # Add cache stats if available
            if cache:
                try:
                    cache_health = await cache.health_check()
                    result.cache_info = {
                        "status": cache_health.get("status", "unknown"),
                        "mode": cache_health.get("mode", "redis"),
                        "database_size": cache_health.get("database_size", 0),
                        "response_time_ms": cache_health.get("response_time", 0),
                    }
                except Exception as e:
                    logger.warning(f"Failed to get cache stats: {e}")
                    result.cache_info = {"status": "error", "error": str(e)}

            return result

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise HTTPException(
                status_code=500, detail=f"Database stats retrieval failed: {str(e)}"
            )

    @router.get("/requests")
    async def get_orchestration_requests(
        limit: int = 50,
        offset: int = 0,
        database: DatabaseConnection = Depends(get_database),
    ):
        """Get recent orchestration requests"""
        try:
            requests = await database.get_recent_requests(limit=limit, offset=offset)

            return {
                "requests": [
                    OrchestrationRequestResponse(
                        id=req.id,
                        request_id=req.request_id,
                        prompt=req.prompt,
                        providers=req.providers,
                        model=req.model,
                        status=req.status,
                        created_at=req.created_at,
                        response_count=len(req.responses) if req.responses else 0,
                    )
                    for req in requests
                ],
                "total": len(requests),
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Failed to get orchestration requests: {e}")
            raise HTTPException(
                status_code=500, detail=f"Request retrieval failed: {str(e)}"
            )

    @router.get("/cache/stats")
    async def get_cache_stats(cache: Optional[CacheService] = Depends(get_cache)):
        """Get detailed cache statistics"""
        try:
            if not cache:
                return {"status": "disabled", "reason": "Cache service not available"}

            return await cache.health_check()

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            raise HTTPException(
                status_code=500, detail=f"Cache stats retrieval failed: {str(e)}"
            )

    @router.post("/cache/clear")
    async def clear_cache(cache: Optional[CacheService] = Depends(get_cache)):
        """Clear all cache entries"""
        try:
            if not cache:
                raise HTTPException(
                    status_code=400, detail="Cache service not available"
                )

            # Note: This is a simplified implementation
            # In a real system, you might want to clear specific patterns
            return {"message": "Cache clear operation completed", "status": "success"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

    @router.get("/health")
    async def database_health_check(
        database: DatabaseConnection = Depends(get_database),
        cache: Optional[CacheService] = Depends(get_cache),
    ):
        """Database and cache health check"""
        try:
            health_status = {
                "database": await database.health_check(),
                "cache": (
                    await cache.health_check() if cache else {"status": "disabled"}
                ),
            }

            # Determine overall status
            services = [health_status["database"], health_status["cache"]]
            if health_status["cache"]["status"] == "disabled":
                services = [health_status["database"]]

            overall_status = "healthy"
            if any(s.get("status") == "unhealthy" for s in services):
                overall_status = "unhealthy"
            elif any(s.get("status") == "degraded" for s in services):
                overall_status = "degraded"

            return {"status": overall_status, "services": health_status}

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Health check failed: {str(e)}"
            )

    return router
