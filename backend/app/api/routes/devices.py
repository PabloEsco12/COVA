"""Device management API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from ..deps import CurrentUser, DBSession
from ...schemas import DeviceCreate, DeviceRead
from ...services.device_service import DeviceService

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=list[DeviceRead])
async def list_devices(db: DBSession, current_user: CurrentUser) -> list[DeviceRead]:
    service = DeviceService(db)
    devices = await service.list_for_user(current_user.id)
    return devices


@router.post("/", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def register_device(payload: DeviceCreate, db: DBSession, current_user: CurrentUser) -> DeviceRead:
    service = DeviceService(db)
    device = await service.register_device(current_user.id, name=payload.name, user_agent=payload.user_agent)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_device(device_id: UUID, db: DBSession, current_user: CurrentUser) -> Response:
    service = DeviceService(db)
    await service.delete_device(device_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
