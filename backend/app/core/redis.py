"""
Utilitaires Redis pour les features temps reel.

Infos utiles:
- Fournit un client partage (mise en cache) et un broker Pub/Sub minimal.
- Utilise redis.asyncio; si REDIS_URL est absent, les appels deviennent no-op.
- Payloads pub/sub sont serialises en JSON pour uniformiser la consommation front/back.
"""

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
    """Retourne le client Redis mis en cache (ou None si non configure)."""
    return _redis_client()


class RealtimeBroker:
    """Facade Pub/Sub sur Redis pour diffuser les evenements temps reel."""

    def __init__(self, redis: aioredis.Redis | None) -> None:
        self.redis = redis

    async def publish_conversation(self, conversation_id: str, payload: dict) -> None:
        """Publie un evenement sur le canal d'une conversation."""
        if not self.redis:
            return
        channel = f"conversation:{conversation_id}"
        await self.redis.publish(channel, json.dumps(payload))

    async def publish_user_event(self, user_id: str, payload: dict) -> None:
        """Publie un evenement destine a un utilisateur (ex: notification)."""
        if not self.redis:
            return
        channel = f"user:{user_id}:events"
        await self.redis.publish(channel, json.dumps(payload))

    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        """Souscrit a un canal et renvoie un iterateur sur les messages JSON ou raw."""
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
