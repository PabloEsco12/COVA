"""WebSocket endpoint for user-level realtime notifications."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ...core.redis import RealtimeBroker
from ...core.security import decode_token
from ...dependencies import get_realtime_broker

notifications_ws_router = APIRouter()


@notifications_ws_router.websocket("/ws/notifications")
async def notifications_ws(
    websocket: WebSocket,
    broker: RealtimeBroker = Depends(get_realtime_broker),
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
    if not user_id:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    redis = broker.redis if broker else None
    if redis is None:
        await websocket.send_text(json.dumps({"event": "error", "detail": "notifications_disabled"}))
        await websocket.close()
        return

    channel = f"user:{user_id}:events"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    await websocket.send_text(json.dumps({"event": "ready"}))

    async def sender() -> None:
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                await websocket.send_text(message.get("data"))
        except WebSocketDisconnect:
            return
        except Exception:
            return

    send_task = None
    try:
        send_task = asyncio.create_task(sender())
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                await websocket.send_text(json.dumps({"event": "pong"}))
    finally:
        if send_task:
            send_task.cancel()
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await websocket.close()
