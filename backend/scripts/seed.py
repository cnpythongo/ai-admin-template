# ruff: noqa: E501
"""Seed script to populate the database with initial data.

Usage:
    uv run python scripts/seed.py

Requires the MySQL database to be running with migrations applied.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import async_session
from app.models.department import Department
from app.models.menu import Menu
from app.models.permission import Permission
from app.models.role import Role
from app.models.system_config import SystemConfig
from app.models.user import User


async def seed() -> None:
    """Seed the database with initial data."""
    async with async_session() as db:
        await _seed_departments(db)
        await _seed_permissions(db)
        await _seed_menus(db)
        await _seed_roles(db)
        await _seed_users(db)
        await _seed_system_configs(db)
        print("Seed completed successfully!")


async def _seed_departments(db: AsyncSession) -> None:
    """Seed departments."""
    result = await db.execute(select(Department).limit(1))
    if result.scalar_one_or_none():
        print("Departments already seeded, skipping...")
        return

    departments = [
        Department(name="总公司", parent_id=None, sort_order=1, status=True),
        Department(name="技术部", parent_id=None, sort_order=2, status=True),
        Department(name="产品部", parent_id=None, sort_order=3, status=True),
        Department(name="运营部", parent_id=None, sort_order=4, status=True),
    ]
    db.add_all(departments)
    await db.commit()
    print(f"Seeded {len(departments)} departments")


async def _seed_permissions(db: AsyncSession) -> None:
    """Seed permissions."""
    result = await db.execute(select(Permission).limit(1))
    if result.scalar_one_or_none():
        print("Permissions already seeded, skipping...")
        return

    permissions = [
        # System management
        Permission(name="系统管理", code="system:manage", type="menu", sort_order=1, status=True),
        Permission(name="用户管理", code="system:user:manage", type="menu", sort_order=2, status=True),
        Permission(name="用户列表", code="system:user:list", type="api", sort_order=1, status=True),
        Permission(name="创建用户", code="system:user:create", type="api", sort_order=2, status=True),
        Permission(name="编辑用户", code="system:user:update", type="api", sort_order=3, status=True),
        Permission(name="删除用户", code="system:user:delete", type="api", sort_order=4, status=True),
        # Role management
        Permission(name="角色管理", code="system:role:manage", type="menu", sort_order=3, status=True),
        Permission(name="角色列表", code="system:role:list", type="api", sort_order=1, status=True),
        Permission(name="创建角色", code="system:role:create", type="api", sort_order=2, status=True),
        Permission(name="编辑角色", code="system:role:update", type="api", sort_order=3, status=True),
        Permission(name="删除角色", code="system:role:delete", type="api", sort_order=4, status=True),
        # Permission management
        Permission(name="权限管理", code="system:permission:manage", type="menu", sort_order=4, status=True),
        Permission(name="权限列表", code="system:permission:list", type="api", sort_order=1, status=True),
        Permission(name="创建权限", code="system:permission:create", type="api", sort_order=2, status=True),
        Permission(name="编辑权限", code="system:permission:update", type="api", sort_order=3, status=True),
        Permission(name="删除权限", code="system:permission:delete", type="api", sort_order=4, status=True),
        # Department management
        Permission(name="部门管理", code="system:department:manage", type="menu", sort_order=5, status=True),
        Permission(name="部门列表", code="system:department:list", type="api", sort_order=1, status=True),
        Permission(name="创建部门", code="system:department:create", type="api", sort_order=2, status=True),
        Permission(name="编辑部门", code="system:department:update", type="api", sort_order=3, status=True),
        Permission(name="删除部门", code="system:department:delete", type="api", sort_order=4, status=True),
        # Menu management
        Permission(name="菜单管理", code="system:menu:manage", type="menu", sort_order=6, status=True),
        Permission(name="菜单列表", code="system:menu:list", type="api", sort_order=1, status=True),
        Permission(name="创建菜单", code="system:menu:create", type="api", sort_order=2, status=True),
        Permission(name="编辑菜单", code="system:menu:update", type="api", sort_order=3, status=True),
        Permission(name="删除菜单", code="system:menu:delete", type="api", sort_order=4, status=True),
        # System config
        Permission(name="系统配置", code="system:config:manage", type="menu", sort_order=7, status=True),
        Permission(name="配置列表", code="system:config:list", type="api", sort_order=1, status=True),
        Permission(name="编辑配置", code="system:config:update", type="api", sort_order=2, status=True),
        # Operation logs
        Permission(name="操作日志", code="system:operation_log:manage", type="menu", sort_order=8, status=True),
        Permission(name="日志列表", code="system:operation_log:list", type="api", sort_order=1, status=True),
    ]
    db.add_all(permissions)
    await db.commit()
    print(f"Seeded {len(permissions)} permissions")


async def _seed_menus(db: AsyncSession) -> None:
    """Seed menus."""
    result = await db.execute(select(Menu).limit(1))
    if result.scalar_one_or_none():
        print("Menus already seeded, skipping...")
        return

    menus = [
        Menu(name="仪表盘", route_path="/dashboard", component="dashboard/index", icon="DashboardOutlined", sort_order=1, status=True),
        Menu(name="系统管理", route_path="/system", component=None, icon="SettingOutlined", sort_order=99, status=True),
        Menu(name="用户管理", route_path="/system/users", component="user/index", icon="UserOutlined", sort_order=1, status=True),
        Menu(name="角色管理", route_path="/system/roles", component="role/index", icon="TeamOutlined", sort_order=2, status=True),
        Menu(name="权限管理", route_path="/system/permissions", component="permission/index", icon="SafetyOutlined", sort_order=3, status=True),
        Menu(name="部门管理", route_path="/system/departments", component="department/index", icon="ApartmentOutlined", sort_order=4, status=True),
        Menu(name="菜单管理", route_path="/system/menus", component="menu/index", icon="MenuOutlined", sort_order=5, status=True),
        Menu(name="系统配置", route_path="/system/configs", component="system-config/index", icon="ConfigProvider", sort_order=6, status=True),
        Menu(name="操作日志", route_path="/system/operation-logs", component="operation-log/index", icon="FileTextOutlined", sort_order=7, status=True),
        Menu(name="个人中心", route_path="/profile", component="profile/index", icon="UserOutlined", sort_order=1, status=True),
    ]
    db.add_all(menus)
    await db.commit()
    print(f"Seeded {len(menus)} menus")


async def _seed_roles(db: AsyncSession) -> None:
    """Seed roles."""
    result = await db.execute(select(Role).limit(1))
    if result.scalar_one_or_none():
        print("Roles already seeded, skipping...")
        return

    roles = [
        Role(name="超级管理员", code="super_admin", status=True, remark="拥有所有系统权限"),
        Role(name="系统管理员", code="admin", status=True, remark="系统管理权限"),
        Role(name="普通用户", code="user", status=True, remark="基础访问权限"),
    ]
    db.add_all(roles)
    await db.commit()
    print(f"Seeded {len(roles)} roles")


async def _seed_users(db: AsyncSession) -> None:
    """Seed users."""
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        print("Users already seeded, skipping...")
        return

    # Get roles
    role_result = await db.execute(select(Role).where(Role.code == "super_admin"))
    super_admin_role = role_result.scalar_one_or_none()

    users = [
        User(
            username="admin",
            password_hash=hash_password("admin123"),
            nickname="系统管理员",
            email="admin@example.com",
            is_superuser=True,
            status=True,
        ),
        User(
            username="user1",
            password_hash=hash_password("123456"),
            nickname="普通用户",
            email="user1@example.com",
            is_superuser=False,
            status=True,
        ),
    ]

    # Assign super_admin role to admin
    if super_admin_role:
        users[0].roles = [super_admin_role]

    db.add_all(users)
    await db.commit()
    print(f"Seeded {len(users)} users")


async def _seed_system_configs(db: AsyncSession) -> None:
    """Seed system configs."""
    result = await db.execute(select(SystemConfig).limit(1))
    if result.scalar_one_or_none():
        print("System configs already seeded, skipping...")
        return

    configs = [
        SystemConfig(key="site_name", value="AI Admin", value_type="string", group="basic", label="站点名称", sort_order=1, status=True),
        SystemConfig(key="site_description", value="AI Admin Dashboard", value_type="string", group="basic", label="站点描述", sort_order=2, status=True),
        SystemConfig(key="logo_url", value="", value_type="string", group="basic", label="Logo URL", sort_order=3, status=True),
        SystemConfig(key="page_size", value="20", value_type="int", group="system", label="默认分页大小", sort_order=1, status=True),
        SystemConfig(key="session_timeout", value="30", value_type="int", group="system", label="会话超时(分钟)", sort_order=2, status=True),
        SystemConfig(key="upload_max_size", value="10", value_type="int", group="system", label="上传文件大小限制(MB)", sort_order=3, status=True),
    ]
    db.add_all(configs)
    await db.commit()
    print(f"Seeded {len(configs)} system configs")


def main() -> None:
    """Entry point."""
    asyncio.run(seed())


if __name__ == "__main__":
    main()
