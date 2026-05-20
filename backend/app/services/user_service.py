from __future__ import annotations

from collections.abc import Sequence

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permission import clear_user_permissions_cache
from app.core.security import hash_password, verify_password
from app.models import user_roles
from app.models.department import Department
from app.models.role import Role
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    ProfileUpdate,
    UserCreate,
    UserUpdate,
)


async def _user_to_response(user: User) -> dict:
    """Convert a User model instance to response dict.

    Relationships (department, roles) must be loaded before calling this.
    """
    roles = user.roles or []
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.avatar,
        "status": user.status,
        "is_superuser": user.is_superuser,
        "department_id": user.department_id,
        "department_name": user.department.name if user.department else None,
        "role_ids": [r.id for r in roles],
        "role_names": [r.name for r in roles],
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


async def get_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    username: str | None = None,
    nickname: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    status: bool | None = None,
    department_id: int | None = None,
    role_id: int | None = None,
) -> tuple[list[dict], int]:
    """Get paginated list of users with multi-condition filters."""
    base_query = select(User).where(User.is_deleted.is_(False))

    if username is not None:
        base_query = base_query.where(User.username.ilike(f"%{username}%"))
    if nickname is not None:
        base_query = base_query.where(User.nickname.ilike(f"%{nickname}%"))
    if email is not None:
        base_query = base_query.where(User.email.ilike(f"%{email}%"))
    if phone is not None:
        base_query = base_query.where(User.phone.ilike(f"%{phone}%"))
    if status is not None:
        base_query = base_query.where(User.status == status)
    if department_id is not None:
        base_query = base_query.where(User.department_id == department_id)
    if role_id is not None:
        base_query = base_query.where(
            User.id.in_(
                select(user_roles.c.user_id).where(user_roles.c.role_id == role_id)
            )
        )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Query paginated users with eager loading
    offset_val = (page - 1) * page_size
    query = (
        base_query
        .options(selectinload(User.roles), selectinload(User.department))
        .order_by(User.id)
        .offset(offset_val)
        .limit(page_size)
    )
    result = await db.execute(query)
    users: Sequence[User] = result.scalars().all()

    items = [await _user_to_response(u) for u in users]

    return items, total


async def get_by_id(db: AsyncSession, user_id: int) -> User:
    """Get user by ID. Raises 404 if not found or deleted."""
    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.is_deleted.is_(False))
        .options(selectinload(User.roles), selectinload(User.department))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在 (id={user_id})",
        )
    return user


async def create(db: AsyncSession, data: UserCreate) -> User:
    """Create a new user. Checks username/email/phone uniqueness."""
    # Check username uniqueness (including soft-deleted)
    result = await db.execute(
        select(User).where(User.username == data.username)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"用户名 '{data.username}' 已存在",
        )

    # Check email uniqueness
    if data.email:
        result = await db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱已被使用",
            )

    # Check phone uniqueness
    if data.phone:
        result = await db.execute(
            select(User).where(User.phone == data.phone)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="手机号已被使用",
            )

    # Default password
    password = data.password or "123456"

    user = User(
        username=data.username,
        password_hash=hash_password(password),
        nickname=data.nickname or data.username,
        email=data.email,
        phone=data.phone,
        status=data.status,
        department_id=data.department_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Assign roles if provided
    if data.role_ids:
        role_result = await db.execute(
            select(Role).where(Role.id.in_(data.role_ids))
        )
        roles = role_result.scalars().all()
        user.roles = list(roles)
        await db.commit()
        await db.refresh(user)

    return user


async def update(db: AsyncSession, user_id: int, data: UserUpdate) -> User:
    """Update a user. Username cannot change."""
    user = await get_by_id(db, user_id)

    # Prevent superuser from being deactivated
    update_data = data.model_dump(exclude_unset=True)
    if user.is_superuser and update_data.get("status") is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用超级管理员账户",
        )

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(
    db: AsyncSession,
    user_id: int,
    current_user: User,
) -> None:
    """Soft delete a user. Cannot delete superuser or self."""
    user = await get_by_id(db, user_id)

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己",
        )

    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能删除超级管理员",
        )

    user.is_deleted = True
    await db.commit()


async def set_status(
    db: AsyncSession,
    user_id: int,
    status_value: bool,
    current_user: User,
) -> User:
    """Set user status. Cannot disable superuser or self."""
    user = await get_by_id(db, user_id)

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己",
        )

    if user.is_superuser and not status_value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能禁用超级管理员",
        )

    user.status = status_value
    await db.commit()
    await db.refresh(user)
    return user


async def reset_password(db: AsyncSession, user_id: int) -> str:
    """Reset user password to the default password.

    Returns the new (default) password.
    """
    user = await get_by_id(db, user_id)

    default_password = "123456"
    user.password_hash = hash_password(default_password)
    await db.commit()

    return default_password


async def update_roles(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    role_ids: list[int],
) -> User:
    """Update user roles (full replace). Clears permission cache."""
    user = await get_by_id(db, user_id)

    # Verify all role IDs exist
    if role_ids:
        role_result = await db.execute(
            select(Role.id).where(Role.id.in_(role_ids))
        )
        existing_ids = {row[0] for row in role_result.fetchall()}
        missing = set(role_ids) - existing_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色不存在: {missing}",
            )

    # Full replace roles
    if role_ids:
        result = await db.execute(
            select(Role).where(Role.id.in_(role_ids))
        )
        user.roles = list(result.scalars().all())
    else:
        user.roles = []

    await db.commit()
    await db.refresh(user)

    # Clear permission cache for this user
    await clear_user_permissions_cache([user.id], redis)

    return user


async def update_department(
    db: AsyncSession,
    user_id: int,
    department_id: int | None,
) -> User:
    """Update user department."""
    user = await get_by_id(db, user_id)

    if department_id is not None:
        result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"部门不存在 (id={department_id})",
            )

    user.department_id = department_id
    await db.commit()
    await db.refresh(user)
    return user


async def update_profile(
    db: AsyncSession,
    user_id: int,
    data: ProfileUpdate,
) -> User:
    """Update current user's own profile."""
    user = await get_by_id(db, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(
    db: AsyncSession,
    user_id: int,
    data: PasswordChange,
) -> None:
    """Change current user's password."""
    user = await get_by_id(db, user_id)

    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确",
        )

    user.password_hash = hash_password(data.new_password)
    await db.commit()
