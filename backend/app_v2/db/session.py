"""Database session configuration for the FastAPI v2 backend."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import settings
from db_v2 import Base  # reuse existing metadata


def _make_async_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+psycopg_async://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


db_url = _make_async_url(settings.DATABASE_URL)
engine = create_async_engine(db_url, echo=False, future=True)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


__all__ = ["engine", "async_session_factory", "get_session", "Base"]
