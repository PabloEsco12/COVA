"""Shared enumeration definitions for ORM models."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """Base class to ensure enums serialize as strings."""

    def __str__(self) -> str:  # pragma: no cover - convenience
        return str(self.value)


class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class ContactStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"


class MessageState(StrEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    DELETED = "deleted"


class InvitationRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class CallType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
