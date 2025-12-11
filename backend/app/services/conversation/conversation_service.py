from __future__ import annotations

"""
Facade ConversationService regroupant les mixins spécialisés.
Les responsabilités sont réparties par domaine pour faciliter la navigation.
"""

from .conversation_attachments import ConversationAttachmentMixin
from .conversation_base import ConversationBase
from .conversation_block import ConversationBlockMixin
from .conversation_crypto import ConversationCryptoMixin
from .conversation_delivery import ConversationDeliveryMixin
from .conversation_invites import ConversationInvitesMixin
from .conversation_members import ConversationMembersMixin
from .conversation_messages import ConversationMessagesMixin
from .conversation_notifications import ConversationNotificationMixin
from .conversation_pins import ConversationPinsMixin


class ConversationService(
    ConversationMessagesMixin,
    ConversationPinsMixin,
    ConversationAttachmentMixin,
    ConversationDeliveryMixin,
    ConversationInvitesMixin,
    ConversationMembersMixin,
    ConversationBlockMixin,
    ConversationNotificationMixin,
    ConversationCryptoMixin,
    ConversationBase,
):
    """Opérations haut niveau sur les conversations, membres et messages."""

    pass
