from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    """Schema for creating a department."""

    name: str = Field(..., min_length=1, max_length=128, description="部门名称")
    parent_id: int | None = Field(None, description="上级部门ID")
    sort_order: int = Field(0, ge=0, description="排序")
    status: bool = Field(True, description="状态")


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""

    name: str | None = Field(None, min_length=1, max_length=128, description="部门名称")
    parent_id: int | None = Field(None, description="上级部门ID")
    sort_order: int | None = Field(None, ge=0, description="排序")
    status: bool | None = Field(None, description="状态")


class DepartmentTreeNode(BaseModel):
    """Schema for department tree node response."""

    id: int
    name: str
    parent_id: int | None
    sort_order: int
    status: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    children: list[DepartmentTreeNode] = []


class DepartmentUserItem(BaseModel):
    """Schema for user item in department user list."""

    id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    status: bool
    created_at: datetime | None = None
