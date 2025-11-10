"""Conversation websocket endpoints."""

from __future__ import annotations

import asyncio
import contextlib
import json
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.redis import RealtimeBroker
from ...core.security import decode_token
from ...dependencies import get_realtime_broker, get_db
from app.models import ConversationMember

ws_router = APIRouter()


@ws_router.websocket("/ws/conversations/{conversation_id}")
async def conversation_ws(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    broker: RealtimeBroker = Depends(get_realtime_broker),
    db: AsyncSession = Depends(get_db),
) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except ValueError:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    stmt = (
        select(ConversationMember.id)
        .where(ConversationMember.conversation_id == conversation_id)
        .where(ConversationMember.user_id == user_id)
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()
    if membership is None:
        await websocket.close(code=4403)
        return

    if broker.redis is None:
        await websocket.send_text(json.dumps({"error": "Realtime disabled"}))
        await websocket.close()
        return

    channel = f"conversation:{conversation_id}"
    pubsub = broker.redis.pubsub()
    await pubsub.subscribe(channel)
    await websocket.send_text(json.dumps({"event": "ready", "conversation_id": str(conversation_id)}))

    async def sender() -> None:
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                await websocket.send_text(message.get("data"))
        except asyncio.CancelledError:
            pass

    send_task = asyncio.create_task(sender())
    try:
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                await asyncio.sleep(0)
    finally:
        send_task.cancel()
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        await websocket.close()
