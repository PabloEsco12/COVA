"""Enumerations used by the next-generation messaging schema."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """Enum whose value serialises as a string."""

    def __str__(self) -> str:  # pragma: no cover - convenience
        return str(self.value)


class OrganizationRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    AUDITOR = "auditor"
    MEMBER = "member"


class UserRole(StrEnum):
    SUPERADMIN = "superadmin"
    SUPPORT = "support"
    MEMBER = "member"


class ContactStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"


class ConversationType(StrEnum):
    DIRECT = "direct"
    GROUP = "group"
    BROADCAST = "broadcast"


class ConversationMemberRole(StrEnum):
    OWNER = "owner"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"


class MembershipState(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INVITED = "invited"
    LEFT = "left"


class MessageType(StrEnum):
    TEXT = "text"
    FILE = "file"
    CALL = "call"
    SYSTEM = "system"


class MessageDeliveryState(StrEnum):
    QUEUED = "queued"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


class CallType(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
    SCREEN = "screen"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    WEBHOOK = "webhook"


class PrivacyRequestType(StrEnum):
    EXPORT = "export"
    DELETION = "deletion"


class PrivacyRequestStatus(StrEnum):
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
