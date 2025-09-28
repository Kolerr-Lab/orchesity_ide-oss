"""
Dependency injection container for Orchesity IDE OSS
Provides centralized service management and dependency resolution
"""

from typing import Optional, Dict, Any, Type, TypeVar
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging

from .config import Settings
from ..database.connection import DatabaseConnection
from ..services.cache import CacheService
from ..services.llm_orchestrator import LLMOrchestratorService
from ..services.metrics import MetricsService
from ..services.health import HealthService

T = TypeVar("T")


@dataclass
class ServiceContainer:
    """Main dependency injection container"""

    settings: Settings
    database: Optional[DatabaseConnection] = None
    cache: Optional[CacheService] = None
    orchestrator: Optional[LLMOrchestratorService] = None
    metrics: Optional[MetricsService] = None
    health: Optional[HealthService] = None

    _services: Dict[str, Any] = None

    def __post_init__(self):
        self._services = {}

    async def initialize(self) -> None:
        """Initialize all services"""
        logger = logging.getLogger(__name__)

        try:
            # Initialize database if not in lightweight mode
            if not self.settings.lightweight_mode:
                self.database = DatabaseConnection(self.settings)
                await self.database.initialize()
                logger.info("Database connection initialized")

                # Initialize cache
                self.cache = CacheService(self.settings)
                await self.cache.initialize()
                logger.info("Cache service initialized")

            # Initialize metrics service
            self.metrics = MetricsService(self.settings)
            await self.metrics.initialize()
            logger.info("Metrics service initialized")

            # Initialize health service
            self.health = HealthService(self.settings, self.database, self.cache)
            await self.health.initialize()
            logger.info("Health service initialized")

            # Initialize LLM orchestrator
            self.orchestrator = LLMOrchestratorService(
                settings=self.settings, cache=self.cache, metrics=self.metrics
            )
            await self.orchestrator.initialize()
            logger.info("LLM orchestrator initialized")

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown all services gracefully"""
        logger = logging.getLogger(__name__)

        try:
            if self.orchestrator:
                await self.orchestrator.shutdown()
                logger.info("LLM orchestrator shutdown")

            if self.health:
                await self.health.shutdown()
                logger.info("Health service shutdown")

            if self.metrics:
                await self.metrics.shutdown()
                logger.info("Metrics service shutdown")

            if self.cache:
                await self.cache.shutdown()
                logger.info("Cache service shutdown")

            if self.database:
                await self.database.shutdown()
                logger.info("Database connection shutdown")

        except Exception as e:
            logger.error(f"Error during service shutdown: {e}")

    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance by type"""
        service_name = service_type.__name__.lower()

        if service_name in self._services:
            return self._services[service_name]

        # Lazy initialization for services that support it
        if service_type == LLMOrchestratorService and self.orchestrator:
            self._services[service_name] = self.orchestrator
            return self.orchestrator
        elif service_type == CacheService and self.cache:
            self._services[service_name] = self.cache
            return self.cache
        elif service_type == MetricsService and self.metrics:
            self._services[service_name] = self.metrics
            return self.metrics
        elif service_type == HealthService and self.health:
            self._services[service_name] = self.health
            return self.health
        elif service_type == DatabaseConnection and self.database:
            self._services[service_name] = self.database
            return self.database

        raise ValueError(f"Service {service_type.__name__} not available")


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container"""
    if _container is None:
        raise RuntimeError(
            "Service container not initialized. Call init_container() first."
        )
    return _container


def init_container(settings: Settings) -> ServiceContainer:
    """Initialize the global service container"""
    global _container
    _container = ServiceContainer(settings=settings)
    return _container


@asynccontextmanager
async def lifespan_context(settings: Settings):
    """FastAPI lifespan context manager for service initialization"""
    container = init_container(settings)
    await container.initialize()

    try:
        yield container
    finally:
        await container.shutdown()
