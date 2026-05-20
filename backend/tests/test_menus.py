"""Tests for menu management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_menu(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a menu."""
    response = await client.post("/api/v1/menus/", json={
        "name": "Dashboard",
        "route_path": "/dashboard",
        "component": "dashboard/index",
        "sort_order": 1,
        "status": True,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "Dashboard"


@pytest.mark.asyncio
async def test_get_menu_tree(client: AsyncClient, auth_headers: dict) -> None:
    """Test getting menu tree."""
    response = await client.get("/api/v1/menus/tree", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_update_menu(client: AsyncClient, auth_headers: dict) -> None:
    """Test updating a menu."""
    create_resp = await client.post("/api/v1/menus/", json={
        "name": "Old Menu",
        "route_path": "/old",
        "component": "old/index",
    }, headers=auth_headers)
    menu_id = create_resp.json()["data"]["id"]

    response = await client.put(f"/api/v1/menus/{menu_id}", json={
        "name": "Updated Menu",
    }, headers=auth_headers)
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "Updated Menu"


@pytest.mark.asyncio
async def test_delete_menu(client: AsyncClient, auth_headers: dict) -> None:
    """Test deleting a menu."""
    create_resp = await client.post("/api/v1/menus/", json={
        "name": "Delete Menu",
        "route_path": "/delete-me",
        "component": "delete/index",
    }, headers=auth_headers)
    menu_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/menus/{menu_id}", headers=auth_headers)
    data = response.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_get_user_menus(client: AsyncClient, auth_headers: dict) -> None:
    """Test getting user menus."""
    # Create a menu first
    await client.post("/api/v1/menus/", json={
        "name": "User Menu Test",
        "route_path": "/user-menu",
        "component": "user-menu/index",
        "status": True,
    }, headers=auth_headers)

    response = await client.get("/api/v1/menus/user-menus", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
