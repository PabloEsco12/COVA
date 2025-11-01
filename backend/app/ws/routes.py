"""WebSocket endpoints for realtime messaging."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core.security import decode_access_token
from ..db.redis import get_redis
from ..db.session import session_scope
from ..services.conversation_service import ConversationService
from ..services.events import EVENT_CHANNEL_TEMPLATE, EVENT_STREAM_TEMPLATE

logger = logging.getLogger(__name__)

router = APIRouter()


def _stream_key(conversation_id: UUID) -> str:
    return EVENT_STREAM_TEMPLATE.format(conversation_id=conversation_id)


def _channel_name(conversation_id: UUID) -> str:
    return EVENT_CHANNEL_TEMPLATE.format(conversation_id=conversation_id)


async def _send_historical_events(redis, websocket: WebSocket, conversation_id: UUID, limit: int = 50) -> None:
    stream_key = _stream_key(conversation_id)
    entries = await redis.xrevrange(stream_key, count=limit)
    for _, data in reversed(entries):
        payload = data.get(b"payload") if isinstance(data, dict) else None
        if not payload:
            continue
        try:
            event = json.loads(payload.decode())
            event.setdefault("replayed", True)
            await websocket.send_json(event)
        except Exception as exc:  # pragma: no cover - logging only
            logger.warning("Failed to replay event", exc_info=exc)


async def _forward_pubsub(pubsub, websocket: WebSocket) -> None:
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = message.get("data")
            if isinstance(data, bytes):
                data = data.decode()
            try:
                await websocket.send_json(json.loads(data))
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to forward websocket event", exc_info=exc)
    except asyncio.CancelledError:
        raise


async def _receive_client_messages(websocket: WebSocket) -> None:
    try:
        while True:
            message = await websocket.receive_text()
            if message.lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        raise
    except Exception:
        logger.debug("WebSocket client receiver ended")


@router.websocket("/conversations/{conversation_id}")
async def conversation_ws(websocket: WebSocket, conversation_id: UUID) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    try:
        user_id = decode_access_token(token)
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return

    async with session_scope() as session:
        service = ConversationService(session)
        try:
            await service.get_for_user(conversation_id, user_id)
        except Exception:
            await websocket.close(code=1008, reason="Access denied")
            return

    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = _channel_name(conversation_id)
    await pubsub.subscribe(channel)

    await websocket.accept()
    await websocket.send_json(
        {
            "type": "connection.ack",
            "conversation_id": str(conversation_id),
        }
    )

    await _send_historical_events(redis, websocket, conversation_id)

    forward_task = asyncio.create_task(_forward_pubsub(pubsub, websocket))
    receiver_task = asyncio.create_task(_receive_client_messages(websocket))

    try:
        done, pending = await asyncio.wait(
            {forward_task, receiver_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
    finally:
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        with contextlib.suppress(Exception):
            await websocket.close()
