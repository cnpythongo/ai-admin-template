from __future__ import annotations

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permission import clear_user_permissions_cache
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User

CACHE_PREFIX = "user_perm:"


async def clear_permissions_cache_for_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """Clear permission cache for all users that have the specified role."""
    result = await db.execute(
        select(User)
        .where(User.roles.any(Role.id == role_id))
        .options(selectinload(User.roles))
    )
    users = result.scalars().all()
    user_ids = [user.id for user in users]
    if user_ids:
        await clear_user_permissions_cache(user_ids, redis)
