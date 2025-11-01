"""Event publishing helpers for Redis realtime."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID

from ..db.redis import get_redis
from ..schemas import MessageRead

EVENT_CHANNEL_TEMPLATE = "conv:{conversation_id}:events"
EVENT_STREAM_TEMPLATE = "conv:{conversation_id}:stream"
STREAM_MAX_LEN = 1000


def _channel_name(conversation_id: UUID) -> str:
    return EVENT_CHANNEL_TEMPLATE.format(conversation_id=conversation_id)


def _stream_name(conversation_id: UUID) -> str:
    return EVENT_STREAM_TEMPLATE.format(conversation_id=conversation_id)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def publish_message_created(message: MessageRead) -> None:
    redis = await get_redis()
    payload = {
        "type": "message.created",
        "conversation_id": str(message.conversation_id),
        "message": message.model_dump(mode="json"),
        "published_at": _iso_now(),
    }
    data = json.dumps(payload)
    await redis.publish(_channel_name(message.conversation_id), data)
    await redis.xadd(
        _stream_name(message.conversation_id),
        {"payload": data},
        maxlen=STREAM_MAX_LEN,
        approximate=True,
    )


async def publish_messages_read(conversation_id: UUID, message_ids: Iterable[UUID], user_id: UUID) -> None:
    ids = [str(mid) for mid in message_ids]
    if not ids:
        return
    redis = await get_redis()
    payload = {
        "type": "message.read",
        "conversation_id": str(conversation_id),
        "message_ids": ids,
        "user_id": str(user_id),
        "published_at": _iso_now(),
    }
    data = json.dumps(payload)
    await redis.publish(_channel_name(conversation_id), data)
    await redis.xadd(
        _stream_name(conversation_id),
        {"payload": data},
        maxlen=STREAM_MAX_LEN,
        approximate=True,
    )
