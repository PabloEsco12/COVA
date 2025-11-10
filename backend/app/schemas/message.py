"""Message analytics schemas."""

from __future__ import annotations

import uuid
from typing import List

from pydantic import BaseModel


class ConversationUnread(BaseModel):
    conversation_id: uuid.UUID
    unread: int


class UnreadSummaryResponse(BaseModel):
    total: int
    conversations: List[ConversationUnread]

