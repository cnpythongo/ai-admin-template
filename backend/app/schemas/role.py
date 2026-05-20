from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

CODE_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class RoleCreate(BaseModel):
    """Schema for creating a new role."""

    name: str = Field(..., min_length=1, max_length=128, description="角色名称")
    code: str = Field(..., min_length=1, max_length=128, description="角色编码")
    status: bool = Field(default=True, description="状态")
    remark: str | None = Field(default=None, max_length=500, description="备注")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code format and auto-lowercase."""
        if not CODE_PATTERN.match(v):
            raise ValueError(
                "角色编码必须以字母开头，只允许字母、数字和下划线"
            )
        return v.lower()


class RoleUpdate(BaseModel):
    """Schema for updating a role. Code is NOT allowed to change."""

    name: str | None = Field(default=None, min_length=1, max_length=128, description="角色名称")
    status: bool | None = Field(default=None, description="状态")
    remark: str | None = Field(default=None, max_length=500, description="备注")


class RoleResponse(BaseModel):
    """Schema for role response."""

    id: int
    name: str
    code: str
    status: bool
    remark: str | None
    created_at: datetime
    updated_at: datetime


class RolePermissionUpdate(BaseModel):
    """Schema for updating role permissions (full replace)."""

    permission_ids: list[int] = Field(..., description="权限ID列表")


class RoleUserItem(BaseModel):
    """Schema for a user item under a role."""

    id: int
    username: str
    nickname: str | None
    email: str | None
    status: bool
