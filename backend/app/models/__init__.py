"""
############################################################
# Package : models (exports des entites SQLAlchemy)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Facilite les imports des entites/enums du schema v2.
# - __all__ expose explicitement les objets partageables.
############################################################
"""

from .base import Base
from .audit import AuditLog
from .auth import EmailConfirmationToken, PasswordResetToken, RefreshToken, TotpSecret
from .contact import ContactInvitation, ContactLink
from .conversation import (
    CallParticipant,
    CallSession,
    Conversation,
    ConversationEncryptionKey,
    ConversationInvite,
    ConversationMember,
    MemberKeyWrap,
)
from .device import Device, PushSubscription, SessionToken
from .enums import (
    CallType,
    ContactStatus,
    ConversationMemberRole,
    ConversationType,
    MembershipState,
    MessageDeliveryState,
    MessageType,
    NotificationChannel,
    OrganizationRole,
    PrivacyRequestStatus,
    PrivacyRequestType,
    UserRole,
)
from .integration import BotAgent, WebhookEndpoint
from .message import Message, MessageAttachment, MessageDelivery, MessagePin, MessageReaction
from .notification import NotificationPreference, OutboundNotification
from .privacy import PrivacyRequest
from .user import (
    Organization,
    OrganizationMembership,
    UserAccount,
    UserProfile,
    UserSecurityState,
    Workspace,
    WorkspaceMembership,
)

__all__ = [
    "Base",
    "AuditLog",
    "EmailConfirmationToken",
    "PasswordResetToken",
    "RefreshToken",
    "TotpSecret",
    "ContactInvitation",
    "ContactLink",
    "CallParticipant",
    "CallSession",
    "Conversation",
    "ConversationEncryptionKey",
    "ConversationInvite",
    "ConversationMember",
    "MemberKeyWrap",
    "Device",
    "PushSubscription",
    "SessionToken",
    "CallType",
    "ContactStatus",
    "ConversationMemberRole",
    "ConversationType",
    "MembershipState",
    "MessageDeliveryState",
    "MessageType",
    "NotificationChannel",
    "OrganizationRole",
    "PrivacyRequestStatus",
    "PrivacyRequestType",
    "UserRole",
    "BotAgent",
    "WebhookEndpoint",
    "Message",
    "MessageAttachment",
    "MessageDelivery",
    "MessagePin",
    "MessageReaction",
    "NotificationPreference",
    "OutboundNotification",
    "PrivacyRequest",
    "Organization",
    "OrganizationMembership",
    "UserAccount",
    "UserProfile",
    "UserSecurityState",
    "Workspace",
    "WorkspaceMembership",
]
