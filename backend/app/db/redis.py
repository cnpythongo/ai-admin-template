from collections.abc import AsyncGenerator

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

redis_pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def get_redis() -> AsyncGenerator[Redis]:
    """FastAPI dependency that provides a Redis connection from the pool."""
    redis = Redis(connection_pool=redis_pool)
    try:
        yield redis
    finally:
        await redis.close()
