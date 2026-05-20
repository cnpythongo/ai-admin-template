"""Tests for permission management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_permission(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a permission."""
    response = await client.post("/api/v1/permissions/", json={
        "name": "User List",
        "code": "system:user:list",
        "type": "api",
        "status": True,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["code"] == "system:user:list"


@pytest.mark.asyncio
async def test_create_permission_invalid_code(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a permission with invalid code format."""
    response = await client.post("/api/v1/permissions/", json={
        "name": "Invalid Code",
        "code": "Invalid Code!",  # Spaces and special chars
        "type": "api",
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] != 0


@pytest.mark.asyncio
async def test_get_permission_tree(client: AsyncClient, auth_headers: dict) -> None:
    """Test getting permission tree."""
    # Create a permission
    await client.post("/api/v1/permissions/", json={
        "name": "Root Permission",
        "code": "system:root",
        "type": "menu",
        "status": True,
    }, headers=auth_headers)

    response = await client.get("/api/v1/permissions/tree", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_update_permission(client: AsyncClient, auth_headers: dict) -> None:
    """Test updating a permission."""
    create_resp = await client.post("/api/v1/permissions/", json={
        "name": "Old Permission",
        "code": "system:old:perm",
        "type": "api",
    }, headers=auth_headers)
    perm_id = create_resp.json()["data"]["id"]

    response = await client.put(f"/api/v1/permissions/{perm_id}", json={
        "name": "Updated Permission",
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "Updated Permission"


@pytest.mark.asyncio
async def test_delete_permission(client: AsyncClient, auth_headers: dict) -> None:
    """Test deleting a permission."""
    create_resp = await client.post("/api/v1/permissions/", json={
        "name": "To Delete",
        "code": "system:delete:test",
        "type": "api",
    }, headers=auth_headers)
    perm_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/permissions/{perm_id}", headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
