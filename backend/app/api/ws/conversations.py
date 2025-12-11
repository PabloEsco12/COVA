"""
Endpoints WebSocket pour les conversations (evenements temps reel + presence).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketState

from ...core.redis import RealtimeBroker
from ...core.security import decode_token
from ...dependencies import get_realtime_broker, get_db
from app.models import ConversationMember
import logging

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/conversations/{conversation_id}")
async def conversation_ws(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    broker: RealtimeBroker = Depends(get_realtime_broker),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Canal WS de conversation: vérifie le token, présence et relaye Pub/Sub Redis."""
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("WS conversation rejected: missing token (conversation_id=%s)", conversation_id)
        await websocket.close(code=4401)
        return
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except ValueError as exc:
        logger.warning(
            "WS conversation rejected: invalid token (conversation_id=%s, error=%s)", conversation_id, exc
        )
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
        logger.warning(
            "WS conversation rejected: user %s not member of conversation %s", user_id, conversation_id
        )
        await websocket.close(code=4403)
        return

    redis = broker.redis if broker else None
    channel = f"conversation:{conversation_id}"
    pubsub = None
    if redis is not None:
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
    else:
        await websocket.send_text(json.dumps({"error": "Realtime disabled"}))

    await websocket.send_text(json.dumps({"event": "ready", "conversation_id": str(conversation_id)}))

    presence_online_key = f"conversation:{conversation_id}:presence:online"
    presence_seen_key = f"conversation:{conversation_id}:presence:last_seen"

    async def build_presence_payload() -> dict | None:
        """Construit un snapshot de présence (online/offline) pour diffusion."""
        if redis is None:
            return None
        snapshot = await redis.hgetall(presence_seen_key)
        online = set(await redis.smembers(presence_online_key))
        now_iso = datetime.now(timezone.utc).isoformat()
        users = []
        for raw_user_id, last_seen in snapshot.items():
            users.append(
                {
                    "user_id": raw_user_id,
                    "status": "online" if raw_user_id in online else "offline",
                    "last_seen": last_seen or now_iso,
                }
            )
        users.sort(key=lambda entry: entry["user_id"])
        return {
            "event": "presence:update",
            "payload": {
                "conversation_id": str(conversation_id),
                "timestamp": now_iso,
                "users": users,
            },
        }

    async def broadcast_presence(include_direct: bool = False) -> None:
        """Diffuse la présence sur le canal conversation et éventuellement au client courant."""
        if broker is None or redis is None:
            return
        payload = await build_presence_payload()
        if not payload:
            return
        await broker.publish_conversation(str(conversation_id), payload)
        if include_direct:
            with contextlib.suppress(Exception):
                await websocket.send_text(json.dumps(payload))

    async def mark_presence_online() -> None:
        """Marque l'utilisateur en ligne et diffuse."""
        if redis is None:
            return
        now_iso = datetime.now(timezone.utc).isoformat()
        await redis.sadd(presence_online_key, str(user_id))
        await redis.hset(presence_seen_key, str(user_id), now_iso)
        await redis.expire(presence_online_key, 3600)
        await redis.expire(presence_seen_key, 3600)
        await broadcast_presence(include_direct=True)

    async def mark_presence_offline() -> None:
        """Marque l'utilisateur hors ligne et diffuse."""
        if redis is None:
            return
        await redis.srem(presence_online_key, str(user_id))
        await redis.hset(presence_seen_key, str(user_id), datetime.now(timezone.utc).isoformat())
        await broadcast_presence()

    async def refresh_presence_loop() -> None:
        """Rafraîchit périodiquement le last_seen tant que la connexion reste ouverte."""
        if redis is None:
            return
        try:
            while True:
                await redis.hset(presence_seen_key, str(user_id), datetime.now(timezone.utc).isoformat())
                await asyncio.sleep(20)
        except asyncio.CancelledError:
            pass

    async def sender() -> None:
        """Écoute le pubsub Redis et pousse vers le WebSocket."""
        if pubsub is None:
            return
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                await websocket.send_text(message.get("data"))
        except asyncio.CancelledError:
            pass

    call_events = {"call:offer", "call:answer", "call:candidate", "call:hangup"}

    async def receiver() -> None:
        """Traite les messages entrants du WebSocket et les relaye via Redis si besoin."""
        try:
            while True:
                try:
                    raw = await websocket.receive_text()
                except WebSocketDisconnect:
                    break
                except Exception:
                    await asyncio.sleep(0)
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                event = data.get("event")
                if event in {"typing:start", "typing:stop"}:
                    if broker:
                        payload = {
                            "event": event,
                            "payload": {
                                "conversation_id": str(conversation_id),
                                "user_id": str(user_id),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        }
                        await broker.publish_conversation(str(conversation_id), payload)
                elif event in call_events:
                    if broker:
                        payload = dict(data.get("payload") or {})
                        payload["conversation_id"] = str(conversation_id)
                        payload["from_user_id"] = str(user_id)
                        if payload.get("target_user_id"):
                            payload["target_user_id"] = str(payload["target_user_id"])
                        await broker.publish_conversation(
                            str(conversation_id),
                            {
                                "event": event,
                                "payload": payload,
                            },
                        )
                elif event == "ping":
                    with contextlib.suppress(Exception):
                        await websocket.send_text(json.dumps({"event": "pong"}))
        finally:
            return

    await mark_presence_online()
    send_task = asyncio.create_task(sender())
    recv_task = asyncio.create_task(receiver())
    presence_task = asyncio.create_task(refresh_presence_loop()) if redis else None
    try:
        await recv_task
    finally:
        send_task.cancel()
        if presence_task:
            presence_task.cancel()
        with contextlib.suppress(Exception):
            if pubsub is not None:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
        if redis:
            await mark_presence_offline()
        if websocket.application_state == WebSocketState.CONNECTED:
            with contextlib.suppress(Exception):
                await websocket.close()
