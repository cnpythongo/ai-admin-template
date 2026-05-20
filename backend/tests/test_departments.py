"""Tests for department management endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_department(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a department."""
    response = await client.post("/api/v1/departments/", json={
        "name": "Test Department",
        "sort_order": 1,
        "status": True,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "Test Department"


@pytest.mark.asyncio
async def test_get_department_tree(client: AsyncClient, auth_headers: dict) -> None:
    """Test getting department tree."""
    # Create a department first
    await client.post("/api/v1/departments/", json={
        "name": "Root Dept",
        "sort_order": 1,
    }, headers=auth_headers)

    response = await client.get("/api/v1/departments/tree", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, auth_headers: dict) -> None:
    """Test updating a department."""
    # Create department
    create_resp = await client.post("/api/v1/departments/", json={
        "name": "Old Name",
        "sort_order": 1,
    }, headers=auth_headers)
    dept_id = create_resp.json()["data"]["id"]

    # Update
    response = await client.put(f"/api/v1/departments/{dept_id}", json={
        "name": "New Name",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_department(client: AsyncClient, auth_headers: dict) -> None:
    """Test deleting a department."""
    # Create department
    create_resp = await client.post("/api/v1/departments/", json={
        "name": "To Delete",
        "sort_order": 1,
    }, headers=auth_headers)
    dept_id = create_resp.json()["data"]["id"]

    # Delete
    response = await client.delete(f"/api/v1/departments/{dept_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
