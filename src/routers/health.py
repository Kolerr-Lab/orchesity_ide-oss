"""
Health check router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from ..models import HealthStatus
from ..core.container import ServiceContainer
from ..services.health import HealthService

logger = logging.getLogger(__name__)


def create_router(container: ServiceContainer) -> APIRouter:
    """Create health router with dependency injection"""
    router = APIRouter()

    def get_health_service() -> HealthService:
        """Dependency injection for health service"""
        return container.get_service(HealthService)

    @router.get("/", response_model=HealthStatus)
    async def health_check(health_service: HealthService = Depends(get_health_service)):
        """Comprehensive health check endpoint"""
        try:
            health_data = await health_service.get_health_status(detailed=False)

            return HealthStatus(
                status=health_data["status"],
                timestamp=health_data["timestamp"],
                uptime=health_data["uptime"],
                services=health_data["services"],
                version=health_data.get("version", "unknown"),
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Health check failed: {str(e)}"
            )

    @router.get("/detailed")
    async def detailed_health_check(
        health_service: HealthService = Depends(get_health_service),
    ):
        """Detailed health check with system information"""
        try:
            return await health_service.get_health_status(detailed=True)

        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Detailed health check failed: {str(e)}"
            )

    @router.get("/service/{service_name}")
    async def service_health_check(
        service_name: str, health_service: HealthService = Depends(get_health_service)
    ):
        """Check health of a specific service"""
        try:
            service_status = await health_service.get_service_status(service_name)
            if service_status is None:
                raise HTTPException(
                    status_code=404, detail=f"Service '{service_name}' not found"
                )

            return service_status

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Service health check failed for {service_name}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Service check failed: {str(e)}"
            )

    @router.get("/ready")
    async def readiness_check(
        health_service: HealthService = Depends(get_health_service),
    ):
        """Kubernetes readiness probe"""
        try:
            is_healthy = await health_service.is_healthy()
            if is_healthy:
                return {"status": "ready"}
            else:
                raise HTTPException(status_code=503, detail="Service not ready")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            raise HTTPException(status_code=503, detail="Readiness check failed")

    @router.get("/live")
    async def liveness_check():
        """Kubernetes liveness probe - basic check"""
        return {"status": "alive", "timestamp": "2024-01-01T00:00:00Z"}

    return router
