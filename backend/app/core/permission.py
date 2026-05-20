from __future__ import annotations

import json
from typing import Annotated

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User

CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "user_perm:"


async def get_user_permissions(
    user_id: int,
    db: AsyncSession,
    redis: Redis,
) -> list[str]:
    """Get user's permission codes, using Redis cache if available.

    1. Try Redis cache first (key: ``user_perm:{user_id}``)
    2. On cache miss, query DB and populate cache
    3. Superusers return ``["*"]`` (wildcard)
    """
    cache_key = f"{CACHE_PREFIX}{user_id}"

    # Try cache
    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)  # type: ignore[no-any-return]

    # Cache miss: query DB with eager-loaded roles and permissions
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        return []

    permissions: list[str] = []
    if user.is_superuser:
        permissions = ["*"]
    else:
        for role in user.roles:
            if role.status:
                for perm in role.permissions:
                    if perm.code not in permissions:
                        permissions.append(perm.code)

    # Populate cache
    await redis.setex(cache_key, CACHE_TTL, json.dumps(permissions))

    return permissions


async def clear_user_permissions_cache(
    user_ids: list[int],
    redis: Redis,
) -> None:
    """Clear permission cache for specified users."""
    if not user_ids:
        return
    keys = [f"{CACHE_PREFIX}{uid}" for uid in user_ids]
    await redis.delete(*keys)


def require_permissions(*required_perms: str):
    """Dependency factory that checks if the current user has the required permissions.

    Usage::

        @router.get("/users")
        async def list_users(
            _: Annotated[None, Depends(require_permissions("system:user:list"))],
        ):
            ...

    Superusers bypass all permission checks.
    """
    async def _checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
    ) -> None:
        # Superusers bypass all checks
        if current_user.is_superuser:
            return

        user_permissions = await get_user_permissions(
            current_user.id, db, redis,
        )

        # Check each required permission
        for perm in required_perms:
            if perm not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: missing '{perm}'",
                )

    return _checker


# Convenience alias for commonly used permission dependencies
PermissionDep = Annotated[None, Depends]
