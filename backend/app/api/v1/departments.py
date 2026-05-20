from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permission import require_permissions
from app.db.session import get_db
from app.schemas.common import PaginatedData, success
from app.schemas.department import (
    DepartmentCreate,
    DepartmentTreeNode,
    DepartmentUpdate,
)
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["部门管理"])


@router.get("/tree")
async def get_department_tree(
    _: Annotated[None, Depends(require_permissions("system:department:list"))],
    db: AsyncSession = Depends(get_db),
):
    """Get department tree structure."""
    tree = await department_service.get_tree(db)
    return success(data=tree)


@router.post("/")
async def create_department(
    data: DepartmentCreate,
    _: Annotated[None, Depends(require_permissions("system:department:create"))],
    db: AsyncSession = Depends(get_db),
):
    """Create a new department."""
    department = await department_service.create(db, data)
    return success(data=DepartmentTreeNode(
        id=department.id,
        name=department.name,
        parent_id=department.parent_id,
        sort_order=department.sort_order,
        status=department.status,
        created_at=department.created_at,
        updated_at=department.updated_at,
    ))


@router.put("/{department_id}")
async def update_department(
    department_id: int,
    data: DepartmentUpdate,
    _: Annotated[None, Depends(require_permissions("system:department:update"))],
    db: AsyncSession = Depends(get_db),
):
    """Update a department."""
    department = await department_service.update(db, department_id, data)
    return success(data=DepartmentTreeNode(
        id=department.id,
        name=department.name,
        parent_id=department.parent_id,
        sort_order=department.sort_order,
        status=department.status,
        created_at=department.created_at,
        updated_at=department.updated_at,
    ))


@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    _: Annotated[None, Depends(require_permissions("system:department:delete"))],
    db: AsyncSession = Depends(get_db),
):
    """Delete a department."""
    await department_service.delete(db, department_id)
    return success(data=None)


@router.get("/{department_id}/users")
async def get_department_users(
    department_id: int,
    _: Annotated[None, Depends(require_permissions("system:department:list"))],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
):
    """Get paginated users in a department."""
    items, total = await department_service.get_users(
        db, department_id, page=page, page_size=page_size,
    )
    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))
