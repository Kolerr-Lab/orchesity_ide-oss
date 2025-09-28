"""
Redis cache service for Orchesity IDE OSS
Handles caching of LLM responses, session data, and temporary storage
"""

import json
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Redis cache service for caching LLM responses and session data"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.is_connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                db=settings.redis_db,
                max_connections=settings.redis_max_connections,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("✅ Connected to Redis successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.is_connected = False
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("🔌 Disconnected from Redis")
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate a consistent cache key from data"""
        # Create a hash of the data for consistent keys
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return f"{prefix}:{data_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                # Update cache metadata
                await self._update_cache_metadata(key, "hit")
                return json.loads(value)
            else:
                await self._update_cache_metadata(key, "miss")
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            expire_time = expire_seconds or settings.cache_expire_seconds
            json_value = json.dumps(value, default=str)
            
            success = await self.redis_client.setex(
                key, 
                expire_time, 
                json_value
            )
            
            if success:
                # Store cache metadata
                await self._store_cache_metadata(key, len(json_value), expire_time)
            
            return bool(success)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            deleted = await self.redis_client.delete(key)
            return bool(deleted)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.is_connected or not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    async def cache_llm_response(
        self, 
        prompt: str, 
        provider: str, 
        model: str,
        response: str,
        tokens_used: Optional[int] = None,
        response_time: float = 0.0
    ) -> str:
        """Cache LLM response with metadata"""
        cache_data = {
            "prompt": prompt,
            "provider": provider,
            "model": model
        }
        
        cache_key = self._generate_cache_key("llm_response", cache_data)
        
        cache_value = {
            "response": response,
            "provider": provider,
            "model": model,
            "tokens_used": tokens_used,
            "response_time": response_time,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        await self.set(cache_key, cache_value)
        logger.info(f"📦 Cached LLM response for {provider}:{model}")
        
        return cache_key
    
    async def get_cached_llm_response(
        self, 
        prompt: str, 
        provider: str, 
        model: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached LLM response"""
        cache_data = {
            "prompt": prompt,
            "provider": provider,
            "model": model
        }
        
        cache_key = self._generate_cache_key("llm_response", cache_data)
        cached_response = await self.get(cache_key)
        
        if cached_response:
            logger.info(f"🎯 Cache hit for {provider}:{model}")
        
        return cached_response
    
    async def cache_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Cache session data"""
        cache_key = f"session:{session_id}"
        return await self.set(cache_key, data, expire_seconds=86400)  # 24 hours
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data"""
        cache_key = f"session:{session_id}"
        return await self.get(cache_key)
    
    async def cache_workflow_result(
        self, 
        workflow_id: str, 
        execution_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """Cache workflow execution result"""
        cache_key = f"workflow_result:{workflow_id}:{execution_id}"
        return await self.set(cache_key, result, expire_seconds=7200)  # 2 hours
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_connected or not self.redis_client:
            return {"error": "Redis not connected"}
        
        try:
            info = await self.redis_client.info()
            
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "is_connected": self.is_connected
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    async def _store_cache_metadata(self, key: str, size: int, expire_seconds: int):
        """Store metadata about cached items"""
        metadata_key = f"cache_meta:{key}"
        metadata = {
            "size": size,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=expire_seconds)).isoformat(),
            "hit_count": 0
        }
        
        # Store metadata with longer expiration
        await self.redis_client.setex(
            metadata_key, 
            expire_seconds + 3600,  # 1 hour longer than actual data
            json.dumps(metadata)
        )
    
    async def _update_cache_metadata(self, key: str, action: str):
        """Update cache metadata on access"""
        metadata_key = f"cache_meta:{key}"
        
        try:
            metadata_json = await self.redis_client.get(metadata_key)
            if metadata_json:
                metadata = json.loads(metadata_json)
                if action == "hit":
                    metadata["hit_count"] = metadata.get("hit_count", 0) + 1
                    metadata["last_accessed"] = datetime.utcnow().isoformat()
                
                # Update metadata
                ttl = await self.redis_client.ttl(metadata_key)
                if ttl > 0:
                    await self.redis_client.setex(
                        metadata_key,
                        ttl,
                        json.dumps(metadata)
                    )
        except Exception as e:
            logger.debug(f"Failed to update cache metadata for {key}: {e}")


# Global cache instance
cache = RedisCache()