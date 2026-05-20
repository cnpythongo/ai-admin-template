from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permission import require_permissions
from app.db.redis import get_redis
from app.db.session import get_db
from app.schemas.common import PaginatedData, success
from app.schemas.role import (
    RoleCreate,
    RolePermissionUpdate,
    RoleResponse,
    RoleUpdate,
)
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["角色管理"])


def _to_role_response(role: object) -> RoleResponse:
    """Convert a Role model instance to RoleResponse."""
    return RoleResponse(
        id=role.id,  # type: ignore[attr-defined]
        name=role.name,  # type: ignore[attr-defined]
        code=role.code,  # type: ignore[attr-defined]
        status=role.status,  # type: ignore[attr-defined]
        remark=role.remark,  # type: ignore[attr-defined]
        created_at=role.created_at,  # type: ignore[attr-defined]
        updated_at=role.updated_at,  # type: ignore[attr-defined]
    )


@router.get("", summary="分页查询角色列表")
async def list_roles(
    _: Annotated[None, Depends(require_permissions("system:role:list"))],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    name: str | None = Query(None, description="角色名称"),
    status: bool | None = Query(None, description="状态"),
):
    """Get paginated list of roles."""
    items, total = await role_service.get_list(
        db, page=page, page_size=page_size, name=name, status=status,
    )
    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.post("", summary="创建角色")
async def create_role(
    data: RoleCreate,
    _: Annotated[None, Depends(require_permissions("system:role:create"))],
    db: AsyncSession = Depends(get_db),
):
    """Create a new role."""
    role = await role_service.create(db, data)
    return success(data=_to_role_response(role))


@router.put("/{id}", summary="更新角色")
async def update_role(
    id: int,
    data: RoleUpdate,
    _: Annotated[None, Depends(require_permissions("system:role:update"))],
    db: AsyncSession = Depends(get_db),
):
    """Update a role. Code is NOT allowed to change."""
    role = await role_service.update(db, id, data)
    return success(data=_to_role_response(role))


@router.delete("/{id}", summary="删除角色")
async def delete_role(
    id: int,
    _: Annotated[None, Depends(require_permissions("system:role:delete"))],
    db: AsyncSession = Depends(get_db),
):
    """Delete a role. Raises 409 if role has users."""
    await role_service.delete_role(db, id)
    return success(data=None)


@router.get("/{id}/permissions", summary="获取角色权限ID列表")
async def get_role_permissions(
    id: int,
    _: Annotated[None, Depends(require_permissions("system:role:list"))],
    db: AsyncSession = Depends(get_db),
):
    """Get permission IDs assigned to a role."""
    permission_ids = await role_service.get_permission_ids(db, id)
    return success(data={"permission_ids": permission_ids})


@router.put("/{id}/permissions", summary="分配角色权限")
async def assign_permissions(
    id: int,
    data: RolePermissionUpdate,
    _: Annotated[None, Depends(require_permissions("system:role:update"))],
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Assign permissions to a role (full replace)."""
    await role_service.update_permissions(db, redis, id, data.permission_ids)
    return success(data=None)


@router.get("/{id}/users", summary="获取角色下的用户列表")
async def list_role_users(
    id: int,
    _: Annotated[None, Depends(require_permissions("system:role:list"))],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
):
    """Get paginated users in a role."""
    items, total = await role_service.get_users(
        db, id, page=page, page_size=page_size,
    )
    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ))
