"""Device management service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.device import Device


class DeviceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[Device]:
        stmt: Select[tuple[Device]] = select(Device).where(Device.user_id == user_id).order_by(Device.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def register_device(self, user_id: UUID, name: str, user_agent: str | None = None, trusted: bool = False) -> Device:
        device = Device(user_id=user_id, name=name, user_agent=user_agent, trusted=trusted)
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def touch_device(self, device: Device) -> None:
        device.last_seen_at = datetime.now(timezone.utc)
        await self.session.commit()

    async def get_for_user(self, device_id: UUID, user_id: UUID) -> Device:
        device = await self.session.get(Device, device_id)
        if device is None or device.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        return device

    async def delete_device(self, device_id: UUID, user_id: UUID) -> None:
        device = await self.get_for_user(device_id, user_id)
        await self.session.delete(device)
        await self.session.commit()

