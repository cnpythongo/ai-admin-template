from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.permission import require_permissions
from app.models.permission import PermissionType
from app.schemas.common import success
from app.schemas.permission import PermissionCreate, PermissionResponse, PermissionUpdate
from app.services.permission_service import PermissionService, get_permission_service

router = APIRouter(prefix="/permissions", tags=["权限管理"])


def _to_permission_response(permission: Any) -> PermissionResponse:
    """Convert a Permission model instance (with children) to PermissionResponse."""
    return PermissionResponse(
        id=permission.id,
        name=permission.name,
        code=permission.code,
        type=permission.type,
        parent_id=permission.parent_id,
        api_path=permission.api_path,
        api_method=permission.api_method,
        sort_order=permission.sort_order,
        status=permission.status,
        remark=permission.remark,
        created_at=permission.created_at,
        updated_at=permission.updated_at,
        children=[
            _to_permission_response(child) for child in permission.children
        ],
    )


@router.get("/tree", summary="获取权限树")
async def get_permission_tree(
    _: Annotated[None, Depends(require_permissions("system:permission:list"))],
    type: PermissionType | None = Query(None, description="权限类型过滤"),
    service: PermissionService = Depends(get_permission_service),
):
    """Get permission tree structure, optionally filtered by type."""
    tree = await service.get_tree(type_filter=type)
    result = [_to_permission_response(p) for p in tree]
    return success(data=result)


@router.post("", summary="创建权限")
async def create_permission(
    _: Annotated[None, Depends(require_permissions("system:permission:create"))],
    data: PermissionCreate,
    service: PermissionService = Depends(get_permission_service),
):
    """Create a new permission."""
    permission = await service.create(data)
    return success(data=_to_permission_response(permission))


@router.put("/{id}", summary="更新权限")
async def update_permission(
    _: Annotated[None, Depends(require_permissions("system:permission:update"))],
    id: int,
    data: PermissionUpdate,
    service: PermissionService = Depends(get_permission_service),
):
    """Update a permission by id."""
    permission = await service.update(id, data)
    return success(data=_to_permission_response(permission))


@router.delete("/{id}", summary="删除权限")
async def delete_permission(
    _: Annotated[None, Depends(require_permissions("system:permission:delete"))],
    id: int,
    service: PermissionService = Depends(get_permission_service),
):
    """Delete a permission by id."""
    await service.delete(id)
    return success(message="删除成功")
