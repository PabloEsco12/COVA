from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select

from app.models import (
    Conversation,
    ConversationMember,
    ConversationMemberRole,
    ConversationType,
    MembershipState,
    UserAccount,
)
from .conversation_base import ConversationBase


class ConversationMembersMixin(ConversationBase):
    """CRUD conversations, membres et rôles."""

    async def list_conversations(self, user: UserAccount) -> list[Conversation]:
        """Liste les conversations actives du user avec préchargement des membres/profils."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Conversation)
            .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
            .where(
                ConversationMember.user_id == user.id,
                ConversationMember.state == MembershipState.ACTIVE,
            )
            .options(
                selectinload(Conversation.members).selectinload(ConversationMember.user).selectinload(UserAccount.profile)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def create_conversation(
        self,
        owner: UserAccount,
        title: str | None,
        participant_ids: list[uuid.UUID],
        conv_type: ConversationType,
    ) -> Conversation:
        """Crée une conversation, ajoute l'owner et les participants valides du même workspace/org."""
        membership = await self._get_primary_membership(owner.id)
        workspace = await self._get_default_workspace(membership)

        conversation = Conversation(
            organization_id=membership.organization_id,
            workspace_id=workspace.id if workspace else None,
            created_by=owner.id,
            title=title,
            type=conv_type,
            extra_metadata={"archived": False},
        )
        owner_member = ConversationMember(
            conversation=conversation,
            user_id=owner.id,
            role=ConversationMemberRole.OWNER,
            state=MembershipState.ACTIVE,
        )
        conversation.members.append(owner_member)

        participants = set(participant_ids)
        participants.discard(owner.id)
        if participants:
            stmt_users = select(UserAccount).where(UserAccount.id.in_(participants))
            result_users = await self.session.execute(stmt_users)
            users = {user.id: user for user in result_users.scalars().all()}
            missing = participants - set(users.keys())
            if missing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid participant IDs")
            for participant_id in users.keys():
                conversation.members.append(
                    ConversationMember(
                        conversation=conversation,
                        user_id=participant_id,
                        role=ConversationMemberRole.MEMBER,
                        state=MembershipState.ACTIVE,
                    )
                )

        self.session.add(conversation)
        await self.session.flush()
        await self._log(owner, "conversation.create", resource_id=str(conversation.id))
        return conversation

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        *,
        actor: UserAccount,
        title: str | None = None,
        topic: str | None = None,
        archived: bool | None = None,
    ) -> Conversation:
        """Met à jour titre/sujet/archivage après vérification que l'acteur est owner."""
        from sqlalchemy.orm import selectinload

        membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(membership)
        conversation = await self.session.get(
            Conversation,
            conversation_id,
            options=(selectinload(Conversation.members),),
        )
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

        changed = False
        normalized_title = None
        normalized_topic = None
        if title is not None:
            normalized_title = (title or "").strip() or None
            if conversation.title != normalized_title:
                conversation.title = normalized_title
                changed = True
        if topic is not None:
            normalized_topic = (topic or "").strip() or None
            if conversation.topic != normalized_topic:
                conversation.topic = normalized_topic
                changed = True
        if archived is not None:
            metadata = self._get_metadata(conversation)
            if bool(metadata.get("archived")) != bool(archived):
                metadata["archived"] = bool(archived)
                conversation.extra_metadata = metadata
                changed = True
        if changed:
            await self.session.flush()
            await self._log(
                actor,
                "conversation.update",
                resource_id=str(conversation_id),
                metadata={"title": normalized_title, "topic": normalized_topic, "archived": archived},
            )
        return await self._load_conversation_with_members(conversation_id)

    async def leave_conversation(self, conversation_id: uuid.UUID, user: UserAccount) -> None:
        """Permet à un membre de quitter; transfère éventuellement le rôle owner si nécessaire."""
        membership = await self._get_membership(conversation_id, user.id)
        if membership.role == ConversationMemberRole.OWNER:
            if not await self._has_other_active_owner(conversation_id, exclude_user_id=user.id):
                replacement = await self._promote_fallback_owner(conversation_id, exclude_user_id=user.id)
                if replacement is None:
                    pass
                else:
                    await self._log(
                        user,
                        "conversation.transfer_owner",
                        resource_id=str(conversation_id),
                        metadata={"replacement_user_id": str(replacement.user_id)},
                    )
        membership.state = MembershipState.LEFT
        membership.muted_until = None
        await self.session.flush()
        await self._log(user, "conversation.leave", resource_id=str(conversation_id))

    async def delete_conversation(self, conversation_id: uuid.UUID, *, actor: UserAccount) -> None:
        """Supprime une conversation après vérification du rôle owner."""
        membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(membership)
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        await self.session.delete(conversation)
        await self.session.flush()
        await self._log(actor, "conversation.delete", resource_id=str(conversation_id))

    async def update_member(
        self,
        conversation_id: uuid.UUID,
        *,
        member_user_id: uuid.UUID,
        actor: UserAccount,
        role: ConversationMemberRole | None = None,
        state: MembershipState | None = None,
        muted_until: datetime | None = None,
    ) -> ConversationMember:
        """Modifie role/statut/mute d'un membre (owner requis) en garantissant la presence d'un owner actif."""
        actor_membership = await self._get_membership(conversation_id, actor.id)
        self._require_owner(actor_membership)

        target = await self._get_membership(conversation_id, member_user_id, active_only=False)
        changed = False

        if role is not None and target.role != role:
            if target.role == ConversationMemberRole.OWNER and role != ConversationMemberRole.OWNER:
                if not await self._has_other_active_owner(conversation_id, exclude_user_id=target.user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Conversation must keep at least one owner.",
                    )
            target.role = role
            changed = True

        if state is not None and target.state != state:
            if target.role == ConversationMemberRole.OWNER and state != MembershipState.ACTIVE:
                if not await self._has_other_active_owner(conversation_id, exclude_user_id=target.user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Conversation must keep at least one owner.",
                    )
            target.state = state
            if state == MembershipState.ACTIVE and target.joined_at is None:
                target.joined_at = datetime.now(timezone.utc)
            changed = True

        if muted_until is not None or target.muted_until is not None:
            if target.muted_until != muted_until:
                target.muted_until = muted_until
                changed = True

        if changed:
            await self.session.flush()
            await self._log(
                actor,
                "conversation.member.update",
                resource_id=str(conversation_id),
                metadata={
                    "member_id": str(target.user_id),
                    "role": target.role.value,
                    "state": target.state.value,
                },
            )
        return target
