"""
Health check router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import asyncio
from ..models import HealthStatus
from ..config import settings
from ..utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=HealthStatus)
async def health_check():
    """Basic health check endpoint"""
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # Check LLM providers (basic connectivity)
        services_status = {
            "cpu": {
                "status": "healthy" if cpu_percent < 90 else "warning",
                "usage_percent": cpu_percent,
            },
            "memory": {
                "status": "healthy" if memory.percent < 90 else "warning",
                "usage_percent": memory.percent,
                "available_mb": memory.available // (1024 * 1024),
            },
        }

        # Check LLM provider configurations and DWA status
        from ..services.llm_orchestrator import orchestrator
        
        try:
            dwa_stats = orchestrator.get_dwa_statistics()
            services_status["dwa"] = {
                "status": "healthy",
                "active_providers": dwa_stats["active_providers"],
                "total_providers": dwa_stats["total_providers"],
                "selection_policy": dwa_stats["selection_policy"]
            }
        except Exception as e:
            services_status["dwa"] = {
                "status": "error",
                "error": str(e)
            }
        
        llm_providers = []
        if settings.openai_api_key:
            llm_providers.append("openai")
        if settings.anthropic_api_key:
            llm_providers.append("anthropic")
        if settings.gemini_api_key:
            llm_providers.append("gemini")
        if settings.grok_api_key:
            llm_providers.append("grok")

        services_status["llm_providers"] = {
            "status": "healthy" if llm_providers else "warning",
            "configured_providers": llm_providers,
            "count": len(llm_providers),
        }

        # Overall status
        unhealthy_services = [
            k for k, v in services_status.items() if v.get("status") != "healthy"
        ]
        overall_status = "unhealthy" if unhealthy_services else "healthy"

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=settings.app_version,
            services=services_status,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/detailed", response_model=HealthStatus)
async def detailed_health_check():
    """Detailed health check with more comprehensive checks"""
    try:
        # Basic health check
        basic_health = await health_check()

        # Add more detailed checks
        detailed_services = dict(basic_health.services)

        # Check concurrent request capacity
        detailed_services["orchestration"] = {
            "status": "healthy",
            "max_concurrent_requests": settings.max_concurrent_requests,
            "routing_strategy": settings.routing_strategy,
        }

        # Check configuration
        config_issues = []
        if not any(
            [
                settings.openai_api_key,
                settings.anthropic_api_key,
                settings.gemini_api_key,
                settings.grok_api_key,
            ]
        ):
            config_issues.append("No LLM API keys configured")

        detailed_services["configuration"] = {
            "status": "healthy" if not config_issues else "warning",
            "issues": config_issues,
        }

        # Update overall status
        unhealthy_services = [
            k for k, v in detailed_services.items() if v.get("status") != "healthy"
        ]
        overall_status = "unhealthy" if unhealthy_services else "healthy"

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=settings.app_version,
            services=detailed_services,
        )

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=503, detail="Detailed health check failed")
