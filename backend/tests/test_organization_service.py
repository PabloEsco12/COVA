import uuid

import pytest
from fastapi import HTTPException

from backend.app.models import OrganizationRole
from backend.app.services.organization_service import OrganizationService


class DummySession:
    def __init__(self) -> None:
        self.flushed = False

    async def flush(self) -> None:
        self.flushed = True


class DummyMembership:
    def __init__(self, *, organization_id: uuid.UUID, role: OrganizationRole) -> None:
        self.id = uuid.uuid4()
        self.organization_id = organization_id
        self.role = role
        self.joined_at = None


@pytest.mark.asyncio
async def test_update_role_requires_admin(monkeypatch):
    session = DummySession()
    service = OrganizationService(session)
    org_id = uuid.uuid4()
    actor = type("Actor", (), {"id": uuid.uuid4()})

    async def fake_get_membership_for_user(user_id):
        return DummyMembership(organization_id=org_id, role=OrganizationRole.MEMBER)

    async def fake_get_membership_by_id(membership_id):
        return DummyMembership(organization_id=org_id, role=OrganizationRole.MEMBER)

    monkeypatch.setattr(service, "get_membership_for_user", fake_get_membership_for_user)
    monkeypatch.setattr(service, "get_membership_by_id", fake_get_membership_by_id)

    with pytest.raises(HTTPException) as exc:
        await service.update_role(actor=actor, membership_id=uuid.uuid4(), role=OrganizationRole.ADMIN)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_promote_member(monkeypatch):
    session = DummySession()
    service = OrganizationService(session)
    org_id = uuid.uuid4()
    actor = type("Actor", (), {"id": uuid.uuid4()})
    target_membership = DummyMembership(organization_id=org_id, role=OrganizationRole.MEMBER)

    async def fake_get_membership_for_user(user_id):
        return DummyMembership(organization_id=org_id, role=OrganizationRole.OWNER)

    async def fake_get_membership_by_id(membership_id):
        return target_membership

    monkeypatch.setattr(service, "get_membership_for_user", fake_get_membership_for_user)
    monkeypatch.setattr(service, "get_membership_by_id", fake_get_membership_by_id)

    updated = await service.update_role(actor=actor, membership_id=uuid.uuid4(), role=OrganizationRole.ADMIN)
    assert updated.role == OrganizationRole.ADMIN
    assert session.flushed is True
