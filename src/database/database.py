"""
Database connection and operations for Orchesity IDE OSS
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database import Database
from typing import AsyncGenerator

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Database URL conversion for asyncpg
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    async_database_url = database_url.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
else:
    async_database_url = database_url

# Create engines
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)

async_engine = create_async_engine(
    async_database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)

# Create async session maker
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Database instance for direct queries
database = Database(async_database_url)

# Metadata
metadata = MetaData()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    # Return dummy session in lightweight mode
    if settings.lightweight_mode:
        # This is a hack to make FastAPI happy, but won't actually be used
        class DummySession:
            async def rollback(self):
                pass

            async def close(self):
                pass

        try:
            yield DummySession()
        except Exception:
            pass
        return

    # Normal database session
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database connection"""
    # Skip database connection in lightweight mode
    if settings.lightweight_mode:
        logger.info("⚡ Lightweight mode: Database connection skipped")
        return

    try:
        await database.connect()
        logger.info("✅ Connected to database successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise


async def close_db():
    """Close database connection"""
    try:
        await database.disconnect()
        logger.info("🔌 Disconnected from database")
    except Exception as e:
        logger.error(f"Failed to close database connection: {e}")


async def create_tables():
    """Create database tables"""
    # Skip table creation in lightweight mode
    if settings.lightweight_mode:
        logger.info("⚡ Lightweight mode: Database tables creation skipped")
        return

    try:
        from .models import Base

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


async def drop_tables():
    """Drop all database tables (for development/testing)"""
    try:
        from .models import Base

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("🗑️ Database tables dropped successfully")
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise
