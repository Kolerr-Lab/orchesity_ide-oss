"""
Cache service for Orchesity IDE OSS
Provides Redis-based caching with proper error handling and metrics
"""

from typing import Optional, Dict, Any, Union
import json
import logging
import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError

from ..core.config import Settings


logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with connection pooling and error handling"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[redis.Redis] = None
        self._is_initialized = False
        # Fallback in-memory cache for lightweight mode
        self._memory_cache: Dict[str, Any] = {}
        self._memory_cache_expiry: Dict[str, float] = {}

    async def initialize(self) -> None:
        """Initialize Redis connection pool"""
        if self._is_initialized:
            return

        try:
            # Use in-memory cache for lightweight mode
            if self.settings.lightweight_mode:
                logger.info("Lightweight mode: Using in-memory cache")
                self._is_initialized = True
                return

            # Parse Redis URL
            redis_url = self.settings.redis_url

            # Create Redis client with connection pooling
            self._client = redis.Redis.from_url(
                redis_url,
                db=self.settings.redis_db,
                max_connections=self.settings.redis_max_connections,
                socket_timeout=self.settings.redis_socket_timeout,
                socket_connect_timeout=self.settings.redis_socket_connect_timeout,
                retry_on_timeout=True,
                decode_responses=True,  # Return strings instead of bytes
            )

            # Test connection
            await self._client.ping()

            self._is_initialized = True
            logger.info("Redis cache connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown Redis connection"""
        if self._client and not self.settings.lightweight_mode:
            await self._client.aclose()
            self._is_initialized = False
            logger.info("Redis cache connection shutdown")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._is_initialized:
            return None

        # Check in-memory cache first (for lightweight mode)
        if self.settings.lightweight_mode:
            return self._get_memory(key)

        try:
            value = await self._client.get(key)
            if value is None:
                return None

            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except RedisError as e:
            logger.warning(f"Redis get error for key '{key}': {e}")
            return None

    async def set(
        self, key: str, value: Any, expire_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional expiration"""
        if not self._is_initialized:
            return False

        # Use in-memory cache for lightweight mode
        if self.settings.lightweight_mode:
            return self._set_memory(key, value, expire_seconds)

        try:
            # Serialize value to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)

            expire_time = expire_seconds or self.settings.cache_expire_seconds
            return await self._client.setex(key, expire_time, value)

        except (RedisError, TypeError) as e:
            logger.warning(f"Redis set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._is_initialized:
            return False

        if self.settings.lightweight_mode:
            return self._delete_memory(key)

        try:
            return bool(await self._client.delete(key))
        except RedisError as e:
            logger.warning(f"Redis delete error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._is_initialized:
            return False

        if self.settings.lightweight_mode:
            return key in self._memory_cache

        try:
            return bool(await self._client.exists(key))
        except RedisError as e:
            logger.warning(f"Redis exists error for key '{key}': {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for key"""
        if not self._is_initialized:
            return False

        if self.settings.lightweight_mode:
            return self._expire_memory(key, seconds)

        try:
            return await self._client.expire(key, seconds)
        except RedisError as e:
            logger.warning(f"Redis expire error for key '{key}': {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get time-to-live for key in seconds"""
        if not self._is_initialized:
            return -1

        if self.settings.lightweight_mode:
            return self._get_memory_ttl(key)

        try:
            return await self._client.ttl(key)
        except RedisError as e:
            logger.warning(f"Redis TTL error for key '{key}': {e}")
            return -1

    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        if not self._is_initialized:
            return {"status": "unhealthy", "error": "Cache not initialized"}

        if self.settings.lightweight_mode:
            return {
                "status": "healthy",
                "mode": "in_memory",
                "cached_items": len(self._memory_cache),
            }

        try:
            import time

            start_time = time.time()
            await self._client.ping()
            response_time = time.time() - start_time

            # Get some basic stats
            info = await self._client.info()
            db_size = info.get("db0", {}).get("keys", 0)

            return {
                "status": "healthy",
                "response_time": round(response_time * 1000, 2),  # ms
                "database_size": db_size,
                "max_connections": self.settings.redis_max_connections,
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    # In-memory cache methods for lightweight mode
    def _get_memory(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        if key not in self._memory_cache:
            return None

        # Check expiration
        if key in self._memory_cache_expiry:
            import time

            if time.time() > self._memory_cache_expiry[key]:
                del self._memory_cache[key]
                del self._memory_cache_expiry[key]
                return None

        value = self._memory_cache[key]
        try:
            return json.loads(value) if isinstance(value, str) else value
        except (json.JSONDecodeError, TypeError):
            return value

    def _set_memory(
        self, key: str, value: Any, expire_seconds: Optional[int] = None
    ) -> bool:
        """Set value in in-memory cache"""
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            self._memory_cache[key] = value

            if expire_seconds:
                import time

                self._memory_cache_expiry[key] = time.time() + expire_seconds
            elif key in self._memory_cache_expiry:
                del self._memory_cache_expiry[key]

            return True
        except (TypeError, ValueError) as e:
            logger.warning(f"Memory cache set error for key '{key}': {e}")
            return False

    def _delete_memory(self, key: str) -> bool:
        """Delete key from in-memory cache"""
        if key in self._memory_cache:
            del self._memory_cache[key]
            if key in self._memory_cache_expiry:
                del self._memory_cache_expiry[key]
            return True
        return False

    def _expire_memory(self, key: str, seconds: int) -> bool:
        """Set expiration for in-memory cache key"""
        if key in self._memory_cache:
            import time

            self._memory_cache_expiry[key] = time.time() + seconds
            return True
        return False

    def _get_memory_ttl(self, key: str) -> int:
        """Get TTL for in-memory cache key"""
        if key not in self._memory_cache_expiry:
            return -1

        import time

        ttl = self._memory_cache_expiry[key] - time.time()
        return max(0, int(ttl))

    @property
    def is_initialized(self) -> bool:
        """Check if cache is initialized"""
        return self._is_initialized
