from __future__ import annotations

from collections.abc import Sequence

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permission import clear_user_permissions_cache
from app.models import role_permissions, user_roles
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate, RoleUserItem


async def get_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    name: str | None = None,
    status: bool | None = None,
) -> tuple[list[dict], int]:
    """Get paginated list of roles with optional filters.

    Returns (items, total_count).
    Each item includes user_count (number of users assigned to the role).
    """
    # Build base query
    base_query = select(Role)

    if name is not None:
        base_query = base_query.where(Role.name.ilike(f"%{name}%"))
    if status is not None:
        base_query = base_query.where(Role.status == status)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Query paginated roles
    offset = (page - 1) * page_size
    query = base_query.order_by(Role.id).offset(offset).limit(page_size)
    result = await db.execute(query)
    roles: Sequence[Role] = result.scalars().all()

    # Build response with user_count
    items: list[dict] = []
    for role in roles:
        # Count users for this role
        user_count_query = select(func.count()).select_from(
            select(user_roles).where(user_roles.c.role_id == role.id).subquery()
        )
        user_count_result = await db.execute(user_count_query)
        user_count = user_count_result.scalar() or 0

        items.append({
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "status": role.status,
            "remark": role.remark,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "user_count": user_count,
        })

    return items, total


async def get_by_id(db: AsyncSession, role_id: int) -> Role:
    """Get role by ID. Raises 404 if not found."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色不存在 (id={role_id})",
        )
    return role


async def create(db: AsyncSession, data: RoleCreate) -> Role:
    """Create a new role. Checks code uniqueness."""
    # Check code uniqueness
    result = await db.execute(select(Role).where(Role.code == data.code))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"角色编码 '{data.code}' 已存在",
        )

    role = Role(
        name=data.name,
        code=data.code,
        status=data.status,
        remark=data.remark,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def update(db: AsyncSession, role_id: int, data: RoleUpdate) -> Role:
    """Update a role. Code is NOT allowed to change."""
    role = await get_by_id(db, role_id)

    update_data = data.model_dump(exclude_unset=True)

    # Code is NOT allowed to change
    if "code" in update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不允许修改角色编码",
        )

    for field, value in update_data.items():
        setattr(role, field, value)

    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role_id: int) -> None:
    """Delete a role. Raises 409 if the role has assigned users."""
    role = await get_by_id(db, role_id)

    # Check for assigned users
    count_result = await db.execute(
        select(func.count()).select_from(
            select(user_roles).where(user_roles.c.role_id == role_id).subquery()
        )
    )
    user_count = count_result.scalar() or 0
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"该角色下还有 {user_count} 名用户，请先移除",
        )

    await db.delete(role)
    await db.commit()


async def update_permissions(
    db: AsyncSession,
    redis: Redis,
    role_id: int,
    permission_ids: list[int],
) -> None:
    """Update role permissions (full replace).

    1. Delete existing role_permissions entries for this role
    2. Insert new role_permissions entries
    3. Query all users with this role
    4. Clear Redis cache for each user
    """
    # Verify role exists
    await get_by_id(db, role_id)

    # 1. Delete existing permissions
    await db.execute(
        sa_delete(role_permissions).where(role_permissions.c.role_id == role_id)
    )

    # 2. Insert new permissions
    if permission_ids:
        values = [
            {"role_id": role_id, "permission_id": pid}
            for pid in permission_ids
        ]
        await db.execute(insert(role_permissions), values)

    await db.commit()

    # 3. Query all users with this role
    user_id_result = await db.execute(
        select(user_roles.c.user_id).where(user_roles.c.role_id == role_id)
    )
    user_ids = [row[0] for row in user_id_result.fetchall()]

    # 4. Clear Redis cache for these users
    if user_ids:
        await clear_user_permissions_cache(user_ids, redis)


async def get_permission_ids(
    db: AsyncSession,
    role_id: int,
) -> list[int]:
    """Get permission IDs assigned to a role."""
    # Verify role exists
    await get_by_id(db, role_id)

    result = await db.execute(
        select(role_permissions.c.permission_id).where(
            role_permissions.c.role_id == role_id
        )
    )
    return [row[0] for row in result.fetchall()]


async def get_users(
    db: AsyncSession,
    role_id: int,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[RoleUserItem], int]:
    """Get paginated users assigned to a role."""
    # Verify role exists
    await get_by_id(db, role_id)

    # Count total users
    count_result = await db.execute(
        select(func.count()).select_from(
            select(user_roles).where(user_roles.c.role_id == role_id).subquery()
        )
    )
    total = count_result.scalar() or 0

    # Query paginated users
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User)
        .join(user_roles, User.id == user_roles.c.user_id)
        .where(user_roles.c.role_id == role_id, ~User.is_deleted)
        .offset(offset)
        .limit(page_size)
        .order_by(User.id)
    )
    users: Sequence[User] = result.scalars().all()

    items = [
        RoleUserItem(
            id=u.id,
            username=u.username,
            nickname=u.nickname,
            email=u.email,
            status=u.status,
        )
        for u in users
    ]
    return items, total
