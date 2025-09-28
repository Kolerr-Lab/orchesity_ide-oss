"""
Database connection management for Orchesity IDE OSS
Provides async SQLAlchemy connection with proper pooling and error handling
"""

from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text
import asyncio

from ..core.config import Settings


logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Async database connection manager with connection pooling"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None
        self._session_factory = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize database connection pool"""
        if self._is_initialized:
            return

        try:
            # Convert sync URL to async URL if needed
            database_url = self.settings.database_url
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )

            # Create async engine with connection pooling
            self._engine = create_async_engine(
                database_url,
                echo=self.settings.database_echo,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=self.settings.database_pool_size,
                max_overflow=self.settings.database_max_overflow,
                pool_timeout=self.settings.database_pool_timeout,
                pool_recycle=self.settings.database_pool_recycle,
                pool_pre_ping=True,  # Enable connection health checks
            )

            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Test connection
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            self._is_initialized = True
            logger.info("Database connection pool initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown database connection pool"""
        if self._engine:
            await self._engine.dispose()
            self._is_initialized = False
            logger.info("Database connection pool shutdown")

    @asynccontextmanager
    async def session(self):
        """Get a database session context manager"""
        if not self._is_initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def execute_raw(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        async with self.session() as session:
            result = await session.execute(text(query), params or {})
            return [dict(row) for row in result.mappings()]

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            start_time = asyncio.get_event_loop().time()

            async with self.session() as session:
                await session.execute(text("SELECT 1 as health_check"))

            response_time = asyncio.get_event_loop().time() - start_time

            return {
                "status": "healthy",
                "response_time": round(response_time * 1000, 2),  # ms
                "pool_size": self.settings.database_pool_size,
                "max_overflow": self.settings.database_max_overflow,
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized"""
        return self._is_initialized
