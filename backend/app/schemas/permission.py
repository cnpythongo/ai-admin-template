from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.permission import PermissionType


class PermissionCreate(BaseModel):
    """Create permission request schema."""

    name: str = Field(..., min_length=1, max_length=128, description="权限名称")
    code: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-z]+:[a-z]+(:[a-z]+)?$",
        description="权限编码 (格式: module:sub:action)",
    )
    type: PermissionType = Field(..., description="权限类型: menu/button/api")
    parent_id: int | None = Field(None, description="上级权限ID")
    api_path: str | None = Field(None, max_length=255, description="API路径 (type=api时必填)")
    api_method: str | None = Field(
        None, max_length=16, description="HTTP方法 (type=api时必填)"
    )
    sort_order: int = Field(0, ge=0, description="排序")
    status: bool = Field(True, description="状态")
    remark: str | None = Field(None, description="备注")

    @model_validator(mode="after")
    def validate_api_fields(self) -> PermissionCreate:
        """Validate that api_path and api_method are required when type is api."""
        if self.type == PermissionType.API:
            if not self.api_path:
                raise ValueError("api_path is required when type is 'api'")
            if not self.api_method:
                raise ValueError("api_method is required when type is 'api'")
        return self


class PermissionUpdate(BaseModel):
    """Update permission request schema.

    NOTE: code field is NOT allowed to change after creation.
    """

    name: str | None = Field(None, min_length=1, max_length=128, description="权限名称")
    parent_id: int | None = Field(None, description="上级权限ID")
    api_path: str | None = Field(None, max_length=255, description="API路径")
    api_method: str | None = Field(None, max_length=16, description="HTTP方法")
    sort_order: int | None = Field(None, ge=0, description="排序")
    status: bool | None = Field(None, description="状态")
    remark: str | None = Field(None, description="备注")

    @model_validator(mode="after")
    def validate_type_change_protection(self) -> PermissionUpdate:
        """Ensure type is not in the update payload (not allowed to change type)."""
        return self


class PermissionResponse(BaseModel):
    """Permission response schema with recursive children."""

    id: int
    name: str
    code: str
    type: PermissionType
    parent_id: int | None = None
    api_path: str | None = None
    api_method: str | None = None
    sort_order: int = 0
    status: bool = True
    remark: str | None = None
    created_at: datetime
    updated_at: datetime
    children: list[PermissionResponse] = []

    model_config = {"from_attributes": True}
