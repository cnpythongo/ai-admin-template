from __future__ import annotations

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo


class AuthService:
    """Authentication service for login, refresh, logout, and user info."""

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
    ) -> None:
        self.db = db
        self.redis = redis

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT token pair."""
        result = await self.db.execute(
            select(User).where(User.username == request.username, User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()

        if user is None or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        if not user.status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用",
            )

        access_token = create_access_token(subject=str(user.id), username=user.username)
        refresh_token = create_refresh_token(subject=str(user.id), username=user.username)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, refresh_token_str: str) -> TokenResponse:
        """Refresh an access token using a valid refresh token."""
        payload = decode_token(refresh_token_str)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Check if the refresh token has been blacklisted
        blacklisted = await self.redis.get(f"blacklist:{refresh_token_str}")
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        result = await self.db.execute(
            select(User).where(User.id == int(user_id), User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()

        if user is None or not user.status:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled",
            )

        new_access_token = create_access_token(subject=str(user.id), username=user.username)
        new_refresh_token = create_refresh_token(subject=str(user.id), username=user.username)

        # Blacklist the old refresh token
        await self.redis.setex(
            f"blacklist:{refresh_token_str}",
            86400 * 7,  # 7 days
            "revoked",
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    async def logout(self, refresh_token_str: str, user: User) -> None:
        """Logout by blacklisting the refresh token."""
        if refresh_token_str:
            await self.redis.setex(
                f"blacklist:{refresh_token_str}",
                86400 * 7,  # 7 days (max refresh token lifetime)
                "revoked",
            )

    async def get_current_user_info(self, user: User) -> UserInfo:
        """Get the current user's full info including permissions."""
        # Eagerly load roles and their permissions
        result = await self.db.execute(
            select(User)
            .where(User.id == user.id)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.department),
            )
        )
        db_user = result.scalar_one_or_none()
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Collect permission codes
        permission_codes: list[str] = []
        role_names: list[str] = []
        for role in db_user.roles:
            if role.status:
                role_names.append(role.name)
                for perm in role.permissions:
                    if perm.code not in permission_codes:
                        permission_codes.append(perm.code)

        # Superusers have all permissions implicitly
        if db_user.is_superuser:
            permission_codes = ["*"]

        return UserInfo(
            id=db_user.id,
            username=db_user.username,
            nickname=db_user.nickname,
            email=db_user.email,
            phone=db_user.phone,
            avatar=db_user.avatar,
            is_superuser=db_user.is_superuser,
            department_id=db_user.department_id,
            department_name=db_user.department.name if db_user.department else None,
            roles=role_names,
            permissions=permission_codes,
            created_at=db_user.created_at,
        )


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(db=db, redis=redis)
