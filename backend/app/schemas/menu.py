from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MenuCreate(BaseModel):
    """Create menu request schema."""

    name: str = Field(..., min_length=1, max_length=128, description="菜单名称")
    icon: str | None = Field(None, max_length=64, description="图标")
    route_path: str = Field(
        ..., min_length=1, max_length=255, description="路由路径"
    )
    component: str | None = Field(
        None, max_length=255, description="组件路径"
    )
    parent_id: int | None = Field(None, description="上级菜单ID")
    sort_order: int = Field(0, ge=0, description="排序")
    hidden: bool = Field(False, description="是否隐藏")
    is_external_link: bool = Field(False, description="是否外链")
    permission_ids: list[int] = Field(
        default_factory=list, description="关联权限ID列表"
    )


class MenuUpdate(BaseModel):
    """Update menu request schema."""

    name: str | None = Field(None, min_length=1, max_length=128, description="菜单名称")
    icon: str | None = Field(None, max_length=64, description="图标")
    route_path: str | None = Field(
        None, min_length=1, max_length=255, description="路由路径"
    )
    component: str | None = Field(
        None, max_length=255, description="组件路径"
    )
    parent_id: int | None = Field(None, description="上级菜单ID")
    sort_order: int | None = Field(None, ge=0, description="排序")
    hidden: bool | None = Field(None, description="是否隐藏")
    is_external_link: bool | None = Field(None, description="是否外链")
    permission_ids: list[int] | None = Field(
        None, description="关联权限ID列表"
    )


class MenuResponse(BaseModel):
    """Menu response schema with recursive children."""

    id: int
    name: str
    icon: str | None = None
    route_path: str | None = None
    component: str | None = None
    parent_id: int | None = None
    sort_order: int = 0
    hidden: bool = False
    is_external_link: bool = False
    status: bool = True
    permission_ids: list[int] = []
    created_at: datetime
    updated_at: datetime
    children: list[MenuResponse] = []

    model_config = {"from_attributes": True}


class UserMenuResponse(BaseModel):
    """User menu response (without permission_ids) for dynamic routing."""

    id: int
    name: str
    icon: str | None = None
    route_path: str | None = None
    component: str | None = None
    parent_id: int | None = None
    sort_order: int = 0
    hidden: bool = False
    is_external_link: bool = False
    children: list[UserMenuResponse] = []

    model_config = {"from_attributes": True}
