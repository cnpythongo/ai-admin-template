"""Tests for role management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a role."""
    response = await client.post("/api/v1/roles", json={
        "name": "Admin Role",
        "code": "admin_role",
        "status": True,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "Admin Role"


@pytest.mark.asyncio
async def test_list_roles(client: AsyncClient, auth_headers: dict) -> None:
    """Test listing roles."""
    # Create a role first
    await client.post("/api/v1/roles", json={
        "name": "Test Role",
        "code": "test_role",
        "status": True,
    }, headers=auth_headers)

    response = await client.get("/api/v1/roles?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient, auth_headers: dict) -> None:
    """Test updating a role."""
    create_resp = await client.post("/api/v1/roles", json={
        "name": "Original Role",
        "code": "original_role",
    }, headers=auth_headers)
    role_id = create_resp.json()["data"]["id"]

    response = await client.put(f"/api/v1/roles/{role_id}", json={
        "name": "Updated Role",
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "Updated Role"


@pytest.mark.asyncio
async def test_delete_role(client: AsyncClient, auth_headers: dict) -> None:
    """Test deleting a role with no users."""
    create_resp = await client.post("/api/v1/roles", json={
        "name": "Delete Role",
        "code": "delete_role",
    }, headers=auth_headers)
    role_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/roles/{role_id}", headers=auth_headers)
    data = response.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_assign_role_permissions(client: AsyncClient, auth_headers: dict) -> None:
    """Test assigning permissions to a role."""
    # Create role
    role_resp = await client.post("/api/v1/roles", json={
        "name": "Perm Role",
        "code": "perm_role",
    }, headers=auth_headers)
    role_id = role_resp.json()["data"]["id"]

    # Create permission
    perm_resp = await client.post("/api/v1/permissions/", json={
        "name": "Test Perm",
        "code": "system:test:perm",
        "type": "api",
    }, headers=auth_headers)
    perm_id = perm_resp.json()["data"]["id"]

    # Assign permissions
    response = await client.put(f"/api/v1/roles/{role_id}/permissions", json={
        "permission_ids": [perm_id],
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
