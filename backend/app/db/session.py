"""
############################################################
# Module : db.session (SQLAlchemy async)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Construit l'engine async et la factory de sessions.
# - Adapte l'URL Postgres pour asyncpg ou psycopg_async si besoin.
#
# Points de vigilance:
# - Engine partage avec metadata Base.
# - Expire_on_commit=False pour conserver les objets hydratés.
############################################################
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import settings
from app.models import Base  # Assure l'import des modèles pour la metadata


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
