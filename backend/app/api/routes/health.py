"""Healthcheck endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="API healthcheck")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

