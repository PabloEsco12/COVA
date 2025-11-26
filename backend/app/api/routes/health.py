"""
############################################################
# Routes : Health (live/ready)
# Auteur  : Valentin Masurelle
# Date    : 2025-06-04
#
# Description:
# - /health/live : teste uniquement le process FastAPI.
# - /health/ready : teste les dependances critiques via TCP (db, redis, minio, clamav).
# - HEALTH_DEBUG affiche les erreurs detaillees.
############################################################
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["health"], prefix="/health")

# Affiche des details techniques quand active
HEALTH_DEBUG = os.getenv("HEALTH_DEBUG", "false").lower() == "true"


async def check_tcp(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str | None]:
    """Verifie si un service ecoute sur host:port via TCP."""
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True, None
    except Exception as exc:  # pragma: no cover - simple sondage
        return False, str(exc)


@router.get("/live", summary="Liveness probe")
async def live() -> Dict[str, str]:
    """Liveness probe minimaliste: process et event loop uniquement."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def ready() -> Dict[str, Any]:
    """Readiness probe: verifie les dependances critiques via TCP."""
    checks = {
        "db": ("db", 5432),
        "redis": ("redis", 6379),
        "minio": ("minio", 9000),
        "clamav": ("clamav", 3310),
    }

    results: Dict[str, str] = {}
    details: Dict[str, str] = {}

    async def run_check(name: str, host: str, port: int) -> None:
        ok, error = await check_tcp(host, port)
        results[name] = "ok" if ok else "down"
        if error and HEALTH_DEBUG:
            details[name] = error

    await asyncio.gather(*(run_check(name, host, port) for name, (host, port) in checks.items()))

    if all(status == "ok" for status in results.values()):
        global_status = "ok"
    elif any(status == "ok" for status in results.values()):
        global_status = "degraded"
    else:
        global_status = "down"

    payload: Dict[str, Any] = {"status": global_status, "services": results}
    if HEALTH_DEBUG:
        payload["details"] = details
    return payload
