from __future__ import annotations

from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentTreeNode,
    DepartmentUpdate,
    DepartmentUserItem,
)


async def get_all_departments(db: AsyncSession) -> Sequence[Department]:
    """Load all departments from DB, ordered by sort_order."""
    result = await db.execute(
        select(Department).order_by(Department.sort_order, Department.id)
    )
    return result.scalars().all()


def build_tree(
    departments: Sequence[Department],
    parent_id: int | None = None,
) -> list[DepartmentTreeNode]:
    """Recursively build department tree from flat list."""
    nodes: list[DepartmentTreeNode] = []
    for dept in departments:
        if dept.parent_id == parent_id:
            children = build_tree(departments, dept.id)
            node = DepartmentTreeNode(
                id=dept.id,
                name=dept.name,
                parent_id=dept.parent_id,
                sort_order=dept.sort_order,
                status=dept.status,
                created_at=dept.created_at,
                updated_at=dept.updated_at,
                children=children,
            )
            nodes.append(node)
    return nodes


async def get_tree(db: AsyncSession) -> list[DepartmentTreeNode]:
    """Get department tree structure."""
    departments = await get_all_departments(db)
    return build_tree(departments)


async def create(db: AsyncSession, data: DepartmentCreate) -> Department:
    """Create a new department.

    Raises 409 if a department with the same name exists under the same parent.
    """
    # Check name uniqueness under the same parent
    query = select(Department).where(
        Department.name == data.name,
        Department.parent_id == data.parent_id,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"同级下已存在名称为 '{data.name}' 的部门",
        )

    department = Department(
        name=data.name,
        parent_id=data.parent_id,
        sort_order=data.sort_order,
        status=data.status,
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)
    return department


async def get_by_id(db: AsyncSession, department_id: int) -> Department:
    """Get department by ID.

    Raises 404 if not found.
    """
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"部门不存在 (id={department_id})",
        )
    return department


def detect_cycle(
    departments: Sequence[Department],
    target_parent_id: int | None,
    self_id: int,
) -> bool:
    """DFS cycle detection.

    Check if setting self_id's parent to target_parent_id would create a cycle.
    Returns True if a cycle would be created.
    """
    if target_parent_id is None:
        return False

    # Build adjacency list for quick lookup
    children_map: dict[int, list[int]] = {}
    for dept in departments:
        pid = dept.parent_id
        if pid is not None:
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(dept.id)

    # DFS from target_parent_id, check if we can reach self_id
    visited: set[int] = set()
    stack = [target_parent_id]
    while stack:
        current = stack.pop()
        if current == self_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        for child_id in children_map.get(current, []):
            stack.append(child_id)

    return False


async def update(
    db: AsyncSession,
    department_id: int,
    data: DepartmentUpdate,
) -> Department:
    """Update a department.

    If parent_id is changed, runs cycle detection (DFS).
    If name is changed, checks uniqueness under the same parent.
    Raises 409 on conflict or cycle detection.
    """
    department = await get_by_id(db, department_id)

    # If name is being updated, check uniqueness under the same parent
    if data.name is not None and data.name != department.name:
        new_parent_id = data.parent_id if data.parent_id is not None else department.parent_id
        query = select(Department).where(
            Department.name == data.name,
            Department.parent_id == new_parent_id,
            Department.id != department_id,
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"同级下已存在名称为 '{data.name}' 的部门",
            )

    # If parent_id is being changed, run cycle detection
    new_parent_id = (
        data.parent_id if data.parent_id is not None
        else department.parent_id
    )
    if (
        data.parent_id is not None
        and data.parent_id != department.parent_id
    ):
        all_depts = await get_all_departments(db)
        if detect_cycle(all_depts, new_parent_id, department_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="移动该部门会导致循环依赖",
            )

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)

    await db.commit()
    await db.refresh(department)
    return department


async def delete(db: AsyncSession, department_id: int) -> None:
    """Delete a department.

    Raises 409 if the department has children or linked users.
    """
    department = await get_by_id(db, department_id)

    # Check for children
    if department.children:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该部门下存在子部门，无法删除",
        )

    # Check for linked users
    result = await db.execute(
        select(User).where(User.department_id == department_id).limit(1)
    )
    linked_user = result.scalar_one_or_none()
    if linked_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该部门下存在用户，无法删除",
        )

    await db.delete(department)
    await db.commit()


async def get_users(
    db: AsyncSession,
    department_id: int,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[DepartmentUserItem], int]:
    """Get paginated users in a department."""
    # Verify department exists
    await get_by_id(db, department_id)

    # Count total users
    count_query = select(User).where(
        User.department_id == department_id,
        ~User.is_deleted,
    )
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    # Query paginated users
    offset = (page - 1) * page_size
    query = (
        select(User)
        .where(
            User.department_id == department_id,
            ~User.is_deleted,
        )
        .offset(offset)
        .limit(page_size)
        .order_by(User.id)
    )
    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        DepartmentUserItem(
            id=u.id,
            username=u.username,
            nickname=u.nickname,
            email=u.email,
            phone=u.phone,
            status=u.status,
            created_at=u.created_at,
        )
        for u in users
    ]
    return items, total
