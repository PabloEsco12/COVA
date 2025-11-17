"""Redis utilities for realtime features."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, AsyncIterator

import json
import redis.asyncio as aioredis

from ..config import settings


@lru_cache()
def _redis_client() -> aioredis.Redis | None:
    url = settings.REDIS_URL
    if not url:
        return None
    return aioredis.from_url(url, decode_responses=True)


async def get_redis() -> aioredis.Redis | None:
    return _redis_client()


class RealtimeBroker:
    """Publish/subscribe helper around Redis."""

    def __init__(self, redis: aioredis.Redis | None) -> None:
        self.redis = redis

    async def publish_conversation(self, conversation_id: str, payload: dict) -> None:
        if not self.redis:
            return
        channel = f"conversation:{conversation_id}"
        await self.redis.publish(channel, json.dumps(payload))

    async def publish_user_event(self, user_id: str, payload: dict) -> None:
        if not self.redis:
            return
        channel = f"user:{user_id}:events"
        await self.redis.publish(channel, json.dumps(payload))

    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        if not self.redis:
            raise RuntimeError("Realtime broker not configured")
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                data = message.get("data")
                if isinstance(data, str):
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        yield {"raw": data}
                else:
                    yield {"raw": data}
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
