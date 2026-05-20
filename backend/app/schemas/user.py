from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=2, max_length=128, description="用户名")
    password: str | None = Field(default=None, min_length=6, max_length=128, description="密码")
    nickname: str | None = Field(default=None, max_length=128, description="昵称")
    email: str | None = Field(default=None, max_length=255, description="邮箱")
    phone: str | None = Field(default=None, max_length=32, description="手机号")
    status: bool = Field(default=True, description="状态")
    department_id: int | None = Field(default=None, description="部门ID")
    role_ids: list[int] | None = Field(default=None, description="角色ID列表")


class UserUpdate(BaseModel):
    """Schema for updating a user. Username cannot change."""

    nickname: str | None = Field(default=None, max_length=128, description="昵称")
    email: str | None = Field(default=None, max_length=255, description="邮箱")
    phone: str | None = Field(default=None, max_length=32, description="手机号")
    status: bool | None = Field(default=None, description="状态")
    department_id: int | None = Field(default=None, description="部门ID")


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    username: str
    nickname: str | None
    email: str | None
    phone: str | None
    avatar: str | None
    status: bool
    is_superuser: bool
    department_id: int | None
    department_name: str | None
    role_ids: list[int] = []
    role_names: list[str] = []
    created_at: datetime
    updated_at: datetime


class UserStatusUpdate(BaseModel):
    """Schema for updating user status."""

    status: bool = Field(..., description="True=启用 False=禁用")


class UserRoleUpdate(BaseModel):
    """Schema for updating user roles (full replace)."""

    role_ids: list[int] = Field(..., description="角色ID列表")


class UserDepartmentUpdate(BaseModel):
    """Schema for updating user department."""

    department_id: int | None = Field(default=None, description="部门ID")


class ProfileUpdate(BaseModel):
    """Schema for current user profile update."""

    nickname: str | None = Field(default=None, max_length=128, description="昵称")
    email: str | None = Field(default=None, max_length=255, description="邮箱")
    phone: str | None = Field(default=None, max_length=32, description="手机号")


class PasswordChange(BaseModel):
    """Schema for changing current user password."""

    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., min_length=1, description="确认新密码")

    @model_validator(mode="after")
    def passwords_match(self) -> PasswordChange:
        if self.new_password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self
