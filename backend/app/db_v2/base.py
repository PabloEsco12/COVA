"""Declarative base for the next-generation schema."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common base class for SQLAlchemy models."""

    __abstract__ = True
