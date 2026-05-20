from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request body."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request body."""

    refresh_token: str


class UserInfo(BaseModel):
    """Current user info response."""

    id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    is_superuser: bool = False
    department_id: int | None = None
    department_name: str | None = None
    roles: list[str] = []
    permissions: list[str] = []
    created_at: datetime | None = None
