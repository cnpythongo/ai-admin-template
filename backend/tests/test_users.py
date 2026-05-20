"""Tests for user management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a user."""
    response = await client.post("/api/v1/users", json={
        "username": "newuser",
        "password": "test123456",
        "nickname": "New User",
        "email": "newuser@example.com",
        "status": True,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["username"] == "newuser"


@pytest.mark.asyncio
async def test_create_duplicate_user(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a user with duplicate username."""
    # Create first user
    await client.post("/api/v1/users", json={
        "username": "duplicate_user",
        "password": "test123456",
        "nickname": "First",
    }, headers=auth_headers)

    # Try creating duplicate
    response = await client.post("/api/v1/users", json={
        "username": "duplicate_user",
        "password": "test123456",
        "nickname": "Second",
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] != 0


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, auth_headers: dict) -> None:
    """Test listing users."""
    response = await client.get("/api/v1/users?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["total"] >= 1  # admin user exists


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, auth_headers: dict) -> None:
    """Test updating a user."""
    # Create a user first
    create_resp = await client.post("/api/v1/users", json={
        "username": "updatable_user",
        "password": "test123456",
        "nickname": "Original",
    }, headers=auth_headers)
    user_id = create_resp.json()["data"]["id"]

    # Update
    response = await client.put(f"/api/v1/users/{user_id}", json={
        "nickname": "Updated Name",
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["nickname"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, auth_headers: dict) -> None:
    """Test soft-deleting a user."""
    create_resp = await client.post("/api/v1/users", json={
        "username": "deletable_user",
        "password": "test123456",
        "nickname": "To Delete",
    }, headers=auth_headers)
    user_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    data = response.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_set_user_status(client: AsyncClient, auth_headers: dict) -> None:
    """Test enabling/disabling a user."""
    create_resp = await client.post("/api/v1/users", json={
        "username": "status_user",
        "password": "test123456",
        "nickname": "Status Test",
    }, headers=auth_headers)
    user_id = create_resp.json()["data"]["id"]

    # Disable
    response = await client.put(f"/api/v1/users/{user_id}/status", json={
        "status": False,
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] is False


@pytest.mark.asyncio
async def test_assign_user_roles(client: AsyncClient, auth_headers: dict) -> None:
    """Test assigning roles to a user."""
    # Create a role first
    role_resp = await client.post("/api/v1/roles", json={
        "name": "Test Role",
        "code": "user_test_role",
    }, headers=auth_headers)
    role_id = role_resp.json()["data"]["id"]

    # Create a user
    user_resp = await client.post("/api/v1/users", json={
        "username": "role_user",
        "password": "test123456",
        "nickname": "Role User",
    }, headers=auth_headers)
    user_id = user_resp.json()["data"]["id"]

    # Assign role
    response = await client.put(f"/api/v1/users/{user_id}/roles", json={
        "role_ids": [role_id],
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
