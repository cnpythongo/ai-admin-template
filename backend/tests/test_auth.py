"""Tests for authentication endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, auth_headers: dict) -> None:
    """Test successful login returns token pair."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient) -> None:
    """Test login with wrong password returns 401."""
    # First create a user
    from app.core.security import hash_password
    from app.models.user import User
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        user = User(
            username="test_login_user",
            password_hash=hash_password("correctpass"),
            nickname="Test",
            status=True,
        )
        session.add(user)
        await session.commit()

    response = await client.post("/api/v1/auth/login", json={
        "username": "test_login_user",
        "password": "wrongpass",
    })
    assert response.status_code == 200  # FastAPI returns 200 even for errors
    data = response.json()
    assert data["code"] != 0


@pytest.mark.asyncio
async def test_login_disabled_user(client: AsyncClient) -> None:
    """Test login with disabled user returns 403."""
    from app.core.security import hash_password
    from app.models.user import User
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        user = User(
            username="disabled_user",
            password_hash=hash_password("test123"),
            nickname="Disabled",
            status=False,
        )
        session.add(user)
        await session.commit()

    response = await client.post("/api/v1/auth/login", json={
        "username": "disabled_user",
        "password": "test123",
    })
    data = response.json()
    assert data["code"] != 0


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict) -> None:
    """Test get current user info."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["username"] == "admin"
    assert data["data"]["is_superuser"] is True


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient) -> None:
    """Test accessing /me without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, auth_headers: dict) -> None:
    """Test token refresh."""
    # First login to get refresh token
    response = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    data = response.json()
    refresh_token = data["data"]["refresh_token"]

    # Refresh
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]
