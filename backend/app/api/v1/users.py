from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.permission import require_permissions
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, success
from app.schemas.user import (
    UserCreate,
    UserDepartmentUpdate,
    UserRoleUpdate,
    UserStatusUpdate,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户管理"])


def _to_user_response(user: object) -> dict:
    """Convert a User model instance to user response dict."""
    roles = getattr(user, "roles", []) or []
    dept = getattr(user, "department", None)
    return {
        "id": user.id,  # type: ignore[attr-defined]
        "username": user.username,  # type: ignore[attr-defined]
        "nickname": user.nickname,  # type: ignore[attr-defined]
        "email": user.email,  # type: ignore[attr-defined]
        "phone": user.phone,  # type: ignore[attr-defined]
        "avatar": user.avatar,  # type: ignore[attr-defined]
        "status": user.status,  # type: ignore[attr-defined]
        "is_superuser": user.is_superuser,  # type: ignore[attr-defined]
        "department_id": user.department_id,  # type: ignore[attr-defined]
        "department_name": dept.name if dept else None,
        "role_ids": [r.id for r in roles],
        "role_names": [r.name for r in roles],
        "created_at": user.created_at,  # type: ignore[attr-defined]
        "updated_at": user.updated_at,  # type: ignore[attr-defined]
    }


@router.get("", summary="分页查询用户列表")
async def list_users(
    _: Annotated[None, Depends(require_permissions("system:user:list"))],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    username: str | None = Query(None, description="用户名"),
    nickname: str | None = Query(None, description="昵称"),
    email: str | None = Query(None, description="邮箱"),
    phone: str | None = Query(None, description="手机号"),
    status: bool | None = Query(None, description="状态"),
    department_id: int | None = Query(None, description="部门ID"),
    role_id: int | None = Query(None, description="角色ID"),
):
    """Get paginated list of users with multi-condition filters."""
    items, total = await user_service.get_list(
        db,
        page=page,
        page_size=page_size,
        username=username,
        nickname=nickname,
        email=email,
        phone=phone,
        status=status,
        department_id=department_id,
        role_id=role_id,
    )
    return success(
        data=PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("", summary="创建用户")
async def create_user(
    data: UserCreate,
    _: Annotated[None, Depends(require_permissions("system:user:create"))],
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    user = await user_service.create(db, data)
    return success(data=_to_user_response(user))


@router.put("/{id}", summary="更新用户")
async def update_user(
    id: int,
    data: UserUpdate,
    _: Annotated[None, Depends(require_permissions("system:user:update"))],
    db: AsyncSession = Depends(get_db),
):
    """Update a user. Username cannot change."""
    user = await user_service.update(db, id, data)
    return success(data=_to_user_response(user))


@router.delete("/{id}", summary="删除用户")
async def delete_user(
    id: int,
    _: Annotated[None, Depends(require_permissions("system:user:delete"))],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a user. Cannot delete superuser or self."""
    await user_service.delete_user(db, id, current_user)
    return success(data=None)


@router.put("/{id}/status", summary="设置用户状态")
async def set_user_status(
    id: int,
    data: UserStatusUpdate,
    _: Annotated[None, Depends(require_permissions("system:user:update"))],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable or disable a user."""
    user = await user_service.set_status(db, id, data.status, current_user)
    return success(data=_to_user_response(user))


@router.post("/{id}/reset-password", summary="重置密码")
async def reset_user_password(
    id: int,
    _: Annotated[None, Depends(require_permissions("system:user:update"))],
    db: AsyncSession = Depends(get_db),
):
    """Reset a user's password to the default password."""
    new_password = await user_service.reset_password(db, id)
    return success(data={"password": new_password}, message="密码已重置")


@router.put("/{id}/roles", summary="分配用户角色")
async def assign_user_roles(
    id: int,
    data: UserRoleUpdate,
    _: Annotated[None, Depends(require_permissions("system:user:update"))],
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Assign roles to a user (full replace)."""
    user = await user_service.update_roles(db, redis, id, data.role_ids)
    return success(data=_to_user_response(user))


@router.put("/{id}/department", summary="分配用户部门")
async def assign_user_department(
    id: int,
    data: UserDepartmentUpdate,
    _: Annotated[None, Depends(require_permissions("system:user:update"))],
    db: AsyncSession = Depends(get_db),
):
    """Assign a department to a user."""
    user = await user_service.update_department(db, id, data.department_id)
    return success(data=_to_user_response(user))
