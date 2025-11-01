"""Aggregate schemas for easy imports."""

from .auth import (
    AuthSession,
    ConfirmEmailResponse,
    LoginRequest,
    LogoutAllResponse,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    TokenPair,
)
from .contact import ContactCreate, ContactRead, ContactRespond, ContactUpdateAlias, ContactUserInfo
from .conversation import (
    ConversationCreate,
    ConversationMemberRead,
    ConversationMemberUser,
    ConversationRead,
    ConversationSettingsUpdate,
    ConversationArchiveRequest,
)
from .device import DeviceCreate, DeviceRead
from .message import (
    MessageAttachmentCreate,
    MessageAttachmentRead,
    MessageAuthor,
    MessageCreate,
    MessageReactionCreate,
    MessageReactionRead,
    MessageRead,
    MessageReadReceipt,
)
from .invitation import InvitationCreate, InvitationCreateResponse, InvitationRead
from .user import UserCreate, UserPrivate, UserRead

__all__ = [
    "RegisterRequest",
    "RegisterResponse",
    "ConfirmEmailResponse",
    "AuthSession",
    "LoginRequest",
    "TokenPair",
    "RefreshRequest",
    "RefreshResponse",
    "LogoutResponse",
    "LogoutAllResponse",
    "UserCreate",
    "UserRead",
    "UserPrivate",
    "ContactCreate",
    "ContactRead",
    "ContactUpdateAlias",
    "ContactRespond",
    "ContactUserInfo",
    "DeviceRead",
    "DeviceCreate",
    "ConversationCreate",
    "ConversationMemberRead",
    "ConversationMemberUser",
    "ConversationRead",
    "ConversationSettingsUpdate",
    "ConversationArchiveRequest",
    "MessageAuthor",
    "MessageCreate",
    "MessageRead",
    "MessageReadReceipt",
    "MessageReactionRead",
    "MessageReactionCreate",
    "MessageAttachmentRead",
    "MessageAttachmentCreate",
    "InvitationCreate",
    "InvitationRead",
    "InvitationCreateResponse",
]
