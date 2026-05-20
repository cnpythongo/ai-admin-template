from __future__ import annotations

import re

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.permission import Permission, PermissionType
from app.schemas.permission import PermissionCreate, PermissionUpdate

CODE_PATTERN = re.compile(r"^[a-z]+:[a-z]+(:[a-z]+)?$")


class PermissionService:
    """Permission management business logic."""

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
    ) -> None:
        self.db = db

    async def get_tree(
        self, type_filter: PermissionType | None = None
    ) -> list[Permission]:
        """Load all permissions and build a tree structure in memory.

        Optionally filter by permission type.
        """
        query = select(Permission).options(
            selectinload(Permission.children),
        )
        if type_filter is not None:
            query = query.where(Permission.type == type_filter)

        result = await self.db.execute(query)
        all_permissions = list(result.scalars().all())

        # Build tree: only top-level permissions (parent_id is None)
        tree = [p for p in all_permissions if p.parent_id is None]

        # Attach children recursively
        self._attach_children(tree, all_permissions)

        # Sort by sort_order
        self._sort_tree(tree)

        return tree

    def _attach_children(
        self, nodes: list[Permission], all_perms: list[Permission]
    ) -> None:
        """Recursively attach children to each node."""
        for node in nodes:
            node.children = [
                p for p in all_perms if p.parent_id == node.id
            ]
            self._sort_tree(node.children)
            if node.children:
                self._attach_children(node.children, all_perms)

    def _sort_tree(self, nodes: list[Permission]) -> None:
        """Sort a list of permissions by sort_order in-place."""
        nodes.sort(key=lambda p: p.sort_order)

    async def create(self, data: PermissionCreate) -> Permission:
        """Create a new permission.

        Validates:
        - Code format matches ``module:sub:action``
        - Code uniqueness
        - api_path + api_method uniqueness for API type
        """
        # Validate code format
        if not CODE_PATTERN.match(data.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限编码格式不正确，必须为 module:sub:action 格式",
            )

        # Check code uniqueness
        existing = await self.db.execute(
            select(Permission).where(Permission.code == data.code)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"权限编码 '{data.code}' 已存在",
            )

        # Check api_path + api_method uniqueness for API type
        if data.type == PermissionType.API and data.api_path and data.api_method:
            existing_api = await self.db.execute(
                select(Permission).where(
                    Permission.api_path == data.api_path,
                    Permission.api_method == data.api_method,
                )
            )
            if existing_api.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"API路径 '{data.api_method} {data.api_path}' 已存在",
                )

        permission = Permission(
            name=data.name,
            code=data.code,
            type=data.type,
            parent_id=data.parent_id,
            api_path=data.api_path,
            api_method=data.api_method,
            sort_order=data.sort_order,
            status=data.status,
            remark=data.remark,
        )
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def update(self, id: int, data: PermissionUpdate) -> Permission:
        """Update a permission.

        Rules:
        - Code is NOT allowed to change (field excluded from PermissionUpdate)
        - Type is NOT allowed to change
        - If parent_id changed, run cycle detection
        """
        permission = await self._get_or_404(id)

        # Track changes for cycle detection
        parent_id_changed = (
            data.parent_id is not None and data.parent_id != permission.parent_id
        )

        # If parent_id is being set to None explicitly, that means remove parent
        if "parent_id" in data.model_dump(exclude_unset=True) and data.parent_id is None:
            parent_id_changed = permission.parent_id is not None

        # Cycle detection: if parent_id changed
        if parent_id_changed and data.parent_id is not None:
            await self._check_cycle(id, data.parent_id)

        # Apply updates (only set fields that were explicitly provided)
        update_data = data.model_dump(exclude_unset=True)

        # Type is not allowed to change
        if "type" in update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不允许修改权限类型",
            )

        for field, value in update_data.items():
            setattr(permission, field, value)

        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def delete(self, id: int) -> None:
        """Delete a permission.

        Checks:
        - No children exist
        - No role references in role_permissions table (raise 409 with count)
        """
        permission = await self._get_or_404(id)

        # Check for children
        result = await self.db.execute(
            select(Permission).where(Permission.parent_id == id)
        )
        children = result.scalars().all()
        if children:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"该权限下存在 {len(children)} 个子权限，请先删除子权限",
            )

        # Check for role references
        from app.models.role import Role

        role_result = await self.db.execute(
            select(Role).where(Role.permissions.any(id=id))
        )
        referencing_roles = role_result.scalars().all()
        if referencing_roles:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"该权限被 {len(referencing_roles)} 个角色引用，请先解除引用",
            )

        await self.db.delete(permission)
        await self.db.commit()

    async def _get_or_404(self, id: int) -> Permission:
        """Get a permission by id or raise 404."""
        result = await self.db.execute(
            select(Permission).where(Permission.id == id)
        )
        permission = result.scalar_one_or_none()
        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"权限 (id={id}) 不存在",
            )
        return permission

    async def _check_cycle(self, permission_id: int, target_parent_id: int) -> None:
        """Check if setting target_parent_id as parent would create a cycle.

        Uses DFS to verify that the current permission's id is not in
        the subtree of the target parent.
        """
        if permission_id == target_parent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将自己设置为上级权限",
            )

        # Load all permissions for DFS
        result = await self.db.execute(
            select(Permission).options(selectinload(Permission.children))
        )
        all_permissions = result.scalars().all()
        perm_map = {p.id: p for p in all_permissions}

        # DFS from target parent
        visited: set[int] = set()
        stack = [target_parent_id]
        while stack:
            current_id = stack.pop()
            if current_id == permission_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不允许设置上级权限：会导致循环引用",
                )
            if current_id in visited:
                continue
            visited.add(current_id)
            current_perm = perm_map.get(current_id)
            if current_perm and current_perm.children:
                for child in current_perm.children:
                    if child.id not in visited:
                        stack.append(child.id)

    async def get_by_id(self, id: int) -> Permission:
        """Get a permission by id (public method)."""
        return await self._get_or_404(id)


async def get_permission_service(
    db: AsyncSession = Depends(get_db),
) -> PermissionService:
    """Dependency provider for PermissionService."""
    return PermissionService(db=db)
