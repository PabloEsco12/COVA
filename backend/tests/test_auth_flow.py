"""Exemple de test d'intégration pour l'authentification FastAPI v2.
Le test est ignoré par défaut ; configurez DATABASE_URL avant de l'activer..
"""

import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.main import app
from backend.app.db.session import get_session

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.mark.skip(reason="Requires running Postgres and isolated database")
async def test_register_and_login_flow(test_client):
    response = await test_client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "Secret123!", "display_name": "Test"},
    )
    assert response.status_code == 201
    login_response = await test_client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "Secret123!"},
    )
    assert login_response.status_code == 200
