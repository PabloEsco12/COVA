"""Async SQLAlchemy session/engine management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_async_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return dsn
    if dsn.startswith("postgresql://"):
        return dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    if dsn.startswith("postgres://"):  # old style
        return dsn.replace("postgres://", "postgresql+asyncpg://", 1)
    return dsn


async def init_db_engine() -> None:
    """Initialise the async SQLAlchemy engine and session factory."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        return

    dsn = _build_async_dsn(settings.DATABASE_URL)
    _engine = create_async_engine(
        dsn,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        future=True,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def dispose_db_engine() -> None:
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database session factory not initialised. Did you call init_db_engine()?")
    session = _session_factory()
    try:
        yield session
    finally:
        await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_scope() as session:
        yield session
