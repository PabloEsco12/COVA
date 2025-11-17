# app/routes/health.py

import asyncio
import os
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter(tags=["health"], prefix="/health")

# Permet d'afficher plus ou moins de détails selon l'environnement
HEALTH_DEBUG = os.getenv("HEALTH_DEBUG", "false").lower() == "true"


async def check_tcp(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str | None]:
    """
    Vérifie si un service écoute sur host:port via une connexion TCP.
    Retourne (ok, erreur éventuelle).
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return True, None
    except Exception as e:
        return False, str(e)


@router.get("/live", summary="Liveness probe")
async def live() -> Dict[str, str]:
    """
    Liveness probe très simple.
    Si cet endpoint répond 200, ça veut dire :
    - le process FastAPI tourne
    - l'event loop répond

    On *ne* teste PAS les dépendances ici.
    """
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def ready() -> Dict[str, Any]:
    """
    Readiness probe : vérifie les dépendances critiques.
    On teste les connexions TCP vers les services :
      - Postgres (db)
      - Redis
      - Minio
      - ClamAV

    Tu peux plus tard remplacer certains checks TCP
    par des requêtes réelles (SELECT 1, ping Redis, etc.).
    """

    checks = {
        "db": ("db", 5432),
        "redis": ("redis", 6379),
        "minio": ("minio", 9000),
        "clamav": ("clamav", 3310),
    }

    results: Dict[str, str] = {}
    details: Dict[str, str] = {}

    async def run_check(name: str, host: str, port: int):
        ok, error = await check_tcp(host, port)
        results[name] = "ok" if ok else "down"
        if error and HEALTH_DEBUG:
            details[name] = error

    tasks = [
        run_check(name, host, port)
        for name, (host, port) in checks.items()
    ]

    await asyncio.gather(*tasks)

    # Statut global
    if all(status == "ok" for status in results.values()):
        global_status = "ok"
    elif any(status == "ok" for status in results.values()):
        global_status = "degraded"
    else:
        global_status = "down"

    payload: Dict[str, Any] = {
        "status": global_status,
        "services": results,
    }
    if HEALTH_DEBUG:
        payload["details"] = details

    return payload
