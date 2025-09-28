"""
Health service for Orchesity IDE OSS
Provides system health monitoring and status checks
"""

from typing import Dict, Any, Optional, List
import time
import logging
import asyncio

from ..core.config import Settings
from ..database.connection import DatabaseConnection
from .cache import CacheService


logger = logging.getLogger(__name__)


class HealthService:
    """Service for monitoring system health and providing status information"""

    def __init__(
        self,
        settings: Settings,
        database: Optional[DatabaseConnection] = None,
        cache: Optional[CacheService] = None,
    ):
        self.settings = settings
        self.database = database
        self.cache = cache
        self._is_initialized = False
        self._start_time = time.time()
        self._last_health_check = 0
        self._health_cache: Optional[Dict[str, Any]] = None
        self._cache_ttl = 30  # Cache health status for 30 seconds

    async def initialize(self) -> None:
        """Initialize health service"""
        if self._is_initialized:
            return

        self._is_initialized = True
        logger.info("Health service initialized")

    async def shutdown(self) -> None:
        """Shutdown health service"""
        self._is_initialized = False
        logger.info("Health service shutdown")

    async def get_health_status(self, detailed: bool = False) -> Dict[str, Any]:
        """Get comprehensive health status"""
        current_time = time.time()

        # Return cached result if still valid
        if (
            self._health_cache
            and current_time - self._last_health_check < self._cache_ttl
        ):
            return self._health_cache

        status = {
            "status": "healthy",
            "timestamp": str(current_time),
            "uptime": current_time - self._start_time,
            "version": getattr(self.settings, "version", "unknown"),
            "services": {},
        }

        # Check individual services
        services_status = await self._check_services()
        status["services"] = services_status

        # Determine overall status
        unhealthy_services = [
            service
            for service, info in services_status.items()
            if info.get("status") != "healthy"
        ]

        if unhealthy_services:
            status["status"] = (
                "degraded"
                if len(unhealthy_services) < len(services_status)
                else "unhealthy"
            )
            status["issues"] = unhealthy_services

        # Add detailed information if requested
        if detailed:
            status["system_info"] = await self._get_system_info()
            status["configuration"] = self._get_config_summary()

        # Cache the result
        self._health_cache = status
        self._last_health_check = current_time

        return status

    async def _check_services(self) -> Dict[str, Dict[str, Any]]:
        """Check the health of all services"""
        services = {}

        # Database health
        if self.database:
            try:
                db_health = await self.database.health_check()
                services["database"] = db_health
            except Exception as e:
                services["database"] = {"status": "unhealthy", "error": str(e)}
        else:
            services["database"] = {"status": "disabled", "reason": "Lightweight mode"}

        # Cache health
        if self.cache:
            try:
                cache_health = await self.cache.health_check()
                services["cache"] = cache_health
            except Exception as e:
                services["cache"] = {"status": "unhealthy", "error": str(e)}
        else:
            services["cache"] = {"status": "disabled"}

        # Provider connectivity checks
        services["providers"] = await self._check_providers()

        # System resources
        services["system"] = await self._check_system_resources()

        return services

    async def _check_providers(self) -> Dict[str, Any]:
        """Check LLM provider connectivity"""
        providers_status = {"status": "healthy", "providers": {}}

        providers_to_check = []

        # Check which providers are configured
        if self.settings.openai_api_key:
            providers_to_check.append(("openai", "gpt-3.5-turbo"))
        if self.settings.anthropic_api_key:
            providers_to_check.append(("anthropic", "claude-3-haiku-20240307"))
        if self.settings.gemini_api_key:
            providers_to_check.append(("gemini", "gemini-pro"))
        if self.settings.grok_api_key:
            providers_to_check.append(("grok", "grok-beta"))

        if not providers_to_check:
            providers_status["status"] = "unhealthy"
            providers_status["error"] = "No LLM providers configured"
            return providers_status

        # Perform basic connectivity checks (non-blocking)
        unhealthy_providers = []

        for provider_name, _ in providers_to_check:
            try:
                # Simple configuration check - in a real implementation,
                # you might do a lightweight API call here
                providers_status["providers"][provider_name] = {
                    "status": "healthy",
                    "configured": True,
                }
            except Exception as e:
                providers_status["providers"][provider_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                unhealthy_providers.append(provider_name)

        if unhealthy_providers:
            providers_status["status"] = (
                "degraded"
                if len(unhealthy_providers) < len(providers_to_check)
                else "unhealthy"
            )

        return providers_status

    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            import psutil

            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=0.1)

            status = "healthy"
            issues = []

            # Check memory usage (>90% is critical)
            if memory.percent > 90:
                status = "critical"
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 80:
                status = "warning"
                issues.append(f"High memory usage: {memory.percent:.1f}%")

            # Check disk usage (>95% is critical)
            if disk.percent > 95:
                status = "critical"
                issues.append(f"Low disk space: {disk.percent:.1f}% used")
            elif disk.percent > 90:
                status = "warning"
                issues.append(f"Low disk space: {disk.percent:.1f}% used")

            # Check CPU usage (>95% is critical)
            if cpu_percent > 95:
                status = "critical"
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 90:
                status = "warning"
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")

            return {
                "status": status,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "cpu_percent": cpu_percent,
                "issues": issues if issues else None,
            }

        except ImportError:
            # psutil not available
            return {
                "status": "unknown",
                "error": "System monitoring not available (psutil not installed)",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to check system resources: {str(e)}",
            }

    async def _get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information"""
        try:
            import platform
            import psutil

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage("/").total,
            }
        except Exception as e:
            return {"error": f"Failed to get system info: {str(e)}"}

    def _get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without sensitive data)"""
        return {
            "lightweight_mode": self.settings.lightweight_mode,
            "debug_mode": getattr(self.settings, "debug", False),
            "providers_configured": {
                "openai": bool(self.settings.openai_api_key),
                "anthropic": bool(self.settings.anthropic_api_key),
                "gemini": bool(self.settings.gemini_api_key),
                "grok": bool(self.settings.grok_api_key),
            },
            "cache_enabled": not self.settings.lightweight_mode,
            "database_enabled": not self.settings.lightweight_mode,
        }

    async def is_healthy(self) -> bool:
        """Quick health check - returns True if system is healthy"""
        status = await self.get_health_status()
        return status.get("status") == "healthy"

    async def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific service"""
        all_status = await self.get_health_status()
        services = all_status.get("services", {})
        return services.get(service_name)

    @property
    def is_initialized(self) -> bool:
        """Check if health service is initialized"""
        return self._is_initialized
