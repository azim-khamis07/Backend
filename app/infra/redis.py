"""Redis client setup and cache helpers."""

import json
from typing import Any, Optional

import redis
from redis import Redis

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Global Redis client instance
_redis_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    """Get or create Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        logger.info("Redis client initialized", extra={"url": settings.REDIS_URL})
    return _redis_client


def close_redis_client() -> None:
    """Close Redis client connection."""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")


class CacheService:
    """Service for caching operations."""

    def __init__(self, redis_client: Optional[Redis] = None) -> None:
        """Initialize cache service."""
        self.redis = redis_client or get_redis_client()
        self.default_ttl = settings.REDIS_CACHE_TTL

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.warning("Cache get error", extra={"key": key, "error": str(e)})
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            serialized = json.dumps(value)
            ttl = ttl or self.default_ttl
            return bool(self.redis.setex(key, ttl, serialized))
        except (TypeError, redis.RedisError) as e:
            logger.warning("Cache set error", extra={"key": key, "error": str(e)})
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            return bool(self.redis.delete(key))
        except redis.RedisError as e:
            logger.warning("Cache delete error", extra={"key": key, "error": str(e)})
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.warning(
                "Cache delete pattern error", extra={"pattern": pattern, "error": str(e)}
            )
            return 0

    def invalidate_patterns(self, patterns: list[str]) -> int:
        """
        Invalidate multiple cache patterns.
        
        Args:
            patterns: List of cache key patterns (supports wildcards)
            
        Returns:
            Total number of keys deleted
        """
        total_deleted = 0
        for pattern in patterns:
            deleted = self.delete_pattern(pattern)
            total_deleted += deleted
            if deleted > 0:
                logger.debug(
                    "Cache pattern invalidated",
                    extra={"pattern": pattern, "keys_deleted": deleted}
                )
        return total_deleted

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis.exists(key))
        except redis.RedisError:
            return False

    def ping(self) -> bool:
        """Ping Redis server to check connectivity."""
        try:
            return self.redis.ping()
        except redis.RedisError:
            return False


# Singleton instance
cache_service = CacheService()
