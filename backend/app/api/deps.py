"""Common FastAPI dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import get_current_user_id
from ..models.user import User
from ..services.user_service import UserService
from ..db.session import get_db_session

DBSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]


async def get_current_user(current_user_id: CurrentUserId, db: DBSession) -> User:
    service = UserService(db)
    user = await service.get_by_id(current_user_id)
    if user is None or not user.is_active or not user.is_confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte inactif ou non confirmé")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
