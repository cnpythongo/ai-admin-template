from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.permission import require_permissions
from app.models.user import User
from app.schemas.common import success
from app.schemas.menu import (
    MenuCreate,
    MenuResponse,
    MenuUpdate,
)
from app.services.menu_service import MenuService, get_menu_service

router = APIRouter(prefix="/menus", tags=["菜单管理"])


def _to_menu_response(menu: Any) -> MenuResponse:
    """Convert a Menu model instance (with children and permissions) to MenuResponse."""
    return MenuResponse(
        id=menu.id,
        name=menu.name,
        icon=menu.icon,
        route_path=menu.route_path,
        component=menu.component,
        parent_id=menu.parent_id,
        sort_order=menu.sort_order,
        hidden=menu.hidden,
        is_external_link=menu.is_external_link,
        status=menu.status,
        permission_ids=[p.id for p in menu.permissions],
        created_at=menu.created_at,
        updated_at=menu.updated_at,
        children=[
            _to_menu_response(child) for child in menu.children
        ],
    )


@router.get("/tree", summary="获取菜单树")
async def get_menu_tree(
    _: Annotated[None, Depends(require_permissions("system:menu:list"))],
    service: MenuService = Depends(get_menu_service),
):
    """Get full menu tree with permissions."""
    tree = await service.get_tree()
    result = [_to_menu_response(m) for m in tree]
    return success(data=result)


@router.get("/user-menus", summary="获取当前用户菜单树")
async def get_user_menus(
    current_user: User = Depends(get_current_user),
    service: MenuService = Depends(get_menu_service),
):
    """Get current user's accessible menu tree for dynamic routing."""
    tree = await service.get_user_menus(current_user.id)
    return success(data=tree)


@router.post("", summary="创建菜单")
async def create_menu(
    _: Annotated[None, Depends(require_permissions("system:menu:create"))],
    data: MenuCreate,
    service: MenuService = Depends(get_menu_service),
):
    """Create a new menu."""
    menu = await service.create(data)
    # Reload with children for full tree response
    tree = await service.get_tree()
    full_menu = next((m for m in _flatten_tree(tree) if m.id == menu.id), menu)
    return success(data=_to_menu_response(full_menu))


@router.put("/{id}", summary="更新菜单")
async def update_menu(
    _: Annotated[None, Depends(require_permissions("system:menu:update"))],
    id: int,
    data: MenuUpdate,
    service: MenuService = Depends(get_menu_service),
):
    """Update a menu by id."""
    menu = await service.update(id, data)
    tree = await service.get_tree()
    full_menu = next((m for m in _flatten_tree(tree) if m.id == menu.id), menu)
    return success(data=_to_menu_response(full_menu))


@router.delete("/{id}", summary="删除菜单")
async def delete_menu(
    _: Annotated[None, Depends(require_permissions("system:menu:delete"))],
    id: int,
    service: MenuService = Depends(get_menu_service),
):
    """Delete a menu by id."""
    await service.delete(id)
    return success(message="删除成功")


def _flatten_tree(nodes: list[Any]) -> list[Any]:
    """Flatten a tree of menus into a list."""
    result: list[Any] = []
    for node in nodes:
        result.append(node)
        if hasattr(node, "children") and node.children:
            result.extend(_flatten_tree(node.children))
    return result
