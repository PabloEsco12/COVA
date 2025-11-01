"""User related domain services."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import get_password_hash, verify_password
from ..models.enums import UserRole
from ..models.user import User


class UserService:
    """Persisted user operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_email_available(self, email: str) -> None:
        if await self.get_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None = None,
        notification_login: bool = False,
        role: UserRole = UserRole.MEMBER,
        is_active: bool = True,
        is_confirmed: bool = False,
    ) -> User:
        await self.ensure_email_available(email)
        if len(password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at most 72 characters",
            )

        user = User(
            email=email.lower(),
            hashed_password=get_password_hash(password),
            display_name=display_name,
            notification_login=notification_login,
            role=role,
            is_active=is_active,
            is_confirmed=is_confirmed,
        )
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError as exc:  # pragma: no cover - double safety
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.get_by_email(email)
        if user is None:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def mark_email_confirmed(self, user: User) -> None:
        if not user.is_confirmed:
            user.is_confirmed = True
            await self.session.flush()

    async def record_totp_failure(self, user: User, *, max_attempts: int = 5, lock_minutes: int = 15) -> None:
        user.failed_totp_attempts = (user.failed_totp_attempts or 0) + 1
        if user.failed_totp_attempts >= max_attempts:
            user.totp_locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
            user.failed_totp_attempts = 0
        await self.session.flush()

    async def reset_totp_failures(self, user: User) -> None:
        if user.failed_totp_attempts or user.totp_locked_until:
            user.failed_totp_attempts = 0
            user.totp_locked_until = None
            await self.session.flush()

    async def set_password(self, user: User, new_password: str) -> None:
        if len(new_password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at most 72 characters",
            )
        user.hashed_password = get_password_hash(new_password)
        await self.session.flush()

    async def ensure_users_exist(self, user_ids: Iterable[UUID]) -> set[UUID]:
        ids = set(user_ids)
        if not ids:
            return set()
        stmt = select(User.id).where(User.id.in_(ids))
        result = await self.session.execute(stmt)
        found = {row[0] for row in result}
        missing = ids - found
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown participants")
        return found
