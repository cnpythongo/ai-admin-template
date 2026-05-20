from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest
from app.schemas.common import success
from app.schemas.user import PasswordChange, ProfileUpdate
from app.services import user_service
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["认证管理"])
bearer_scheme = HTTPBearer(auto_error=False)


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
        "role_names": [r.name for r in roles],
        "created_at": user.created_at,  # type: ignore[attr-defined]
        "updated_at": user.updated_at,  # type: ignore[attr-defined]
    }


@router.post("/login", summary="用户登录")
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user with username and password, return JWT token pair."""
    result = await auth_service.login(request)
    return success(data=result)


@router.post("/refresh", summary="刷新令牌")
async def refresh(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using a valid refresh token."""
    result = await auth_service.refresh(request.refresh_token)
    return success(data=result)


@router.post("/logout", summary="用户登出")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    """Logout by blacklisting the refresh token."""
    refresh_token_str = ""
    if credentials:
        refresh_token_str = credentials.credentials
    await auth_service.logout(refresh_token_str, current_user)
    return success(message="已登出")


@router.get("/me", summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get the current authenticated user's information and permissions."""
    result = await auth_service.get_current_user_info(current_user)
    return success(data=result)


@router.put("/me", summary="更新个人资料")
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile (nickname, email, phone)."""
    user = await user_service.update_profile(db, current_user.id, data)
    return success(data=_to_user_response(user))


@router.put("/me/password", summary="修改密码")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    await user_service.change_password(db, current_user.id, data)
    return success(data=None)
