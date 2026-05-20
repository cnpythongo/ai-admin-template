from __future__ import annotations

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permission import get_user_permissions
from app.db.redis import get_redis
from app.db.session import get_db
from app.models import menu_permissions
from app.models.menu import Menu
from app.models.permission import Permission
from app.schemas.menu import MenuCreate, MenuUpdate


class MenuService:
    """Menu management business logic."""

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
    ) -> None:
        self.db = db
        self.redis = redis

    async def get_tree(self) -> list[Menu]:
        """Load all menus with permissions and build a tree structure in memory."""
        result = await self.db.execute(
            select(Menu)
            .options(
                selectinload(Menu.permissions),
                selectinload(Menu.children),
            )
            .order_by(Menu.sort_order)
        )
        all_menus = list(result.scalars().all())

        # Build tree: only top-level menus (parent_id is None)
        tree = [m for m in all_menus if m.parent_id is None]

        # Attach children recursively
        self._attach_children(tree, all_menus)

        # Sort by sort_order
        self._sort_tree(tree)

        return tree

    def _attach_children(
        self, nodes: list[Menu], all_menus: list[Menu]
    ) -> None:
        """Recursively attach children to each node."""
        for node in nodes:
            node.children = [
                m for m in all_menus if m.parent_id == node.id
            ]
            self._sort_tree(node.children)
            if node.children:
                self._attach_children(node.children, all_menus)

    def _sort_tree(self, nodes: list[Menu]) -> None:
        """Sort a list of menus by sort_order in-place."""
        nodes.sort(key=lambda m: m.sort_order)

    async def create(self, data: MenuCreate) -> Menu:
        """Create a new menu.

        Validates:
        - route_path global uniqueness
        """
        # Check route_path uniqueness
        existing = await self.db.execute(
            select(Menu).where(Menu.route_path == data.route_path)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"路由路径 '{data.route_path}' 已存在",
            )

        menu = Menu(
            name=data.name,
            icon=data.icon,
            route_path=data.route_path,
            component=data.component,
            parent_id=data.parent_id,
            sort_order=data.sort_order,
            hidden=data.hidden,
            is_external_link=data.is_external_link,
        )
        self.db.add(menu)
        await self.db.flush()

        # Sync permission associations
        if data.permission_ids:
            await self._sync_permissions(menu.id, data.permission_ids)

        await self.db.commit()
        await self.db.refresh(menu)

        # Eagerly load permissions for the response
        result = await self.db.execute(
            select(Menu)
            .where(Menu.id == menu.id)
            .options(selectinload(Menu.permissions))
        )
        menu = result.scalar_one()
        return menu

    async def update(self, id: int, data: MenuUpdate) -> Menu:
        """Update a menu.

        Rules:
        - If route_path changed, check global uniqueness
        - If parent_id changed, run cycle detection
        - permission_ids triggers full replacement
        """
        menu = await self._get_or_404(id)

        update_data = data.model_dump(exclude_unset=True)

        # Check route_path uniqueness if changed
        if "route_path" in update_data and update_data["route_path"] is not None:
            if update_data["route_path"] != menu.route_path:
                existing = await self.db.execute(
                    select(Menu).where(
                        Menu.route_path == update_data["route_path"],
                        Menu.id != id,
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"路由路径 '{update_data['route_path']}' 已存在",
                    )

        # Cycle detection: if parent_id changed
        parent_id_changed = (
            "parent_id" in update_data
            and update_data["parent_id"] != menu.parent_id
        )
        if parent_id_changed and update_data.get("parent_id") is not None:
            await self._check_cycle(id, update_data["parent_id"])

        # Sync permission associations (full replace)
        if "permission_ids" in update_data:
            perm_ids = update_data.pop("permission_ids")
            await self._sync_permissions(id, perm_ids)

        # Apply updates (skip permission_ids and None parent_id marker)
        for field, value in update_data.items():
            if field == "permission_ids":
                continue
            setattr(menu, field, value)

        await self.db.commit()
        await self.db.refresh(menu)

        # Reload with permissions
        result = await self.db.execute(
            select(Menu)
            .where(Menu.id == id)
            .options(selectinload(Menu.permissions))
        )
        menu = result.scalar_one()
        return menu

    async def delete(self, id: int) -> None:
        """Delete a menu.

        Checks:
        - No children exist (409 if children found)
        """
        menu = await self._get_or_404(id)

        # Check for children
        result = await self.db.execute(
            select(Menu).where(Menu.parent_id == id)
        )
        children = result.scalars().all()
        if children:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"该菜单下存在 {len(children)} 个子菜单，请先删除子菜单",
            )

        await self.db.delete(menu)
        await self.db.commit()

    async def get_user_menus(self, user_id: int) -> list[dict]:
        """Get menus accessible to the current user based on permissions.

        Returns a list of dicts (not Menu objects) to avoid SQLAlchemy
        lazy-loading issues during serialization.

        Logic:
        1. Get user's permission codes from Redis cache
        2. Load all menus with their permissions
        3. Filter: a menu is visible if it has no permission_ids (public),
           or at least one of its permission_ids matches the user's permissions
        4. Preserve parent structure: a parent is visible if any child is visible
        """
        # Get user's permission codes
        user_perms = await get_user_permissions(user_id, self.db, self.redis)
        is_superuser = "*" in user_perms

        # Load all menus with permissions
        result = await self.db.execute(
            select(Menu)
            .options(
                selectinload(Menu.permissions),
            )
            .order_by(Menu.sort_order)
        )
        all_menus = list(result.scalars().all())

        # Build parent-child mapping
        menu_map: dict[int, Menu] = {m.id: m for m in all_menus}
        children_map: dict[int | None, list[Menu]] = {}
        for m in all_menus:
            pid = m.parent_id
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(m)

        # Determine which menus are visible
        visible_ids: set[int] = set()

        def is_menu_visible(menu: Menu) -> bool:
            if is_superuser:
                return True
            if not menu.permissions:
                return True
            menu_perm_codes = {p.code for p in menu.permissions}
            return bool(menu_perm_codes & set(user_perms))

        def mark_visible(menu_ids: list[int]) -> None:
            for mid in menu_ids:
                menu = menu_map.get(mid)
                if menu is None:
                    continue
                if is_menu_visible(menu):
                    visible_ids.add(mid)
                child_ids = [
                    c.id for c in children_map.get(mid, [])
                ]
                if child_ids:
                    mark_visible(child_ids)
                    if any(cid in visible_ids for cid in child_ids):
                        visible_ids.add(mid)

        root_ids = [m.id for m in children_map.get(None, [])]
        mark_visible(root_ids)

        def menu_to_dict(menu: Menu) -> dict:
            return {
                "id": menu.id,
                "name": menu.name,
                "icon": menu.icon,
                "route_path": menu.route_path,
                "component": menu.component,
                "parent_id": menu.parent_id,
                "sort_order": menu.sort_order,
                "hidden": menu.hidden,
                "is_external_link": menu.is_external_link,
            }

        def build_filtered_tree(parent_id: int | None) -> list[dict]:
            result_nodes: list[dict] = []
            children = children_map.get(parent_id, [])
            for child in sorted(children, key=lambda m: m.sort_order):
                if child.id not in visible_ids:
                    continue
                node = menu_to_dict(child)
                node["children"] = build_filtered_tree(child.id)
                result_nodes.append(node)
            return result_nodes

        return build_filtered_tree(None)

    async def _sync_permissions(
        self, menu_id: int, permission_ids: list[int]
    ) -> None:
        """Sync menu-permission associations (full replace).

        Deletes all existing associations for the menu, then inserts new ones.
        """
        # Delete existing associations
        await self.db.execute(
            menu_permissions.delete().where(
                menu_permissions.c.menu_id == menu_id
            )
        )

        # Insert new associations
        if permission_ids:
            # Verify all permission IDs exist
            result = await self.db.execute(
                select(Permission.id).where(
                    Permission.id.in_(permission_ids)
                )
            )
            existing_ids = {row[0] for row in result.all()}
            invalid_ids = set(permission_ids) - existing_ids
            if invalid_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权限ID {invalid_ids} 不存在",
                )

            await self.db.execute(
                menu_permissions.insert(),
                [
                    {"menu_id": menu_id, "permission_id": pid}
                    for pid in permission_ids
                ],
            )

    async def _get_or_404(self, id: int) -> Menu:
        """Get a menu by id or raise 404."""
        result = await self.db.execute(
            select(Menu)
            .where(Menu.id == id)
            .options(selectinload(Menu.permissions))
        )
        menu = result.scalar_one_or_none()
        if menu is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"菜单 (id={id}) 不存在",
            )
        return menu

    async def _check_cycle(
        self, menu_id: int, target_parent_id: int
    ) -> None:
        """Check if setting target_parent_id as parent would create a cycle.

        Uses DFS to verify that the current menu's id is not in
        the subtree of the target parent.
        """
        if menu_id == target_parent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将自己设置为上级菜单",
            )

        # Load all menus for DFS
        result = await self.db.execute(
            select(Menu).options(selectinload(Menu.children))
        )
        all_menus = result.scalars().all()
        menu_map = {m.id: m for m in all_menus}

        # DFS from target parent
        visited: set[int] = set()
        stack = [target_parent_id]
        while stack:
            current_id = stack.pop()
            if current_id == menu_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不允许设置上级菜单：会导致循环引用",
                )
            if current_id in visited:
                continue
            visited.add(current_id)
            current_menu = menu_map.get(current_id)
            if current_menu and current_menu.children:
                for child in current_menu.children:
                    if child.id not in visited:
                        stack.append(child.id)


async def get_menu_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MenuService:
    """Dependency provider for MenuService."""
    return MenuService(db=db, redis=redis)
