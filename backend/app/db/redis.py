"""Redis connection utilities."""

from __future__ import annotations

from redis.asyncio import Redis

from ..core.config import settings

redis_client: Redis | None = None


async def get_redis() -> Redis:
    global redis_client  # noqa: PLW0603
    if redis_client is None:
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)
    return redis_client
