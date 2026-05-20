"""Database seed script.

Creates initial data: admin user, default department, permissions, menus, roles, configs.
Run after alembic upgrade head.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import async_session
from app.models import menu_permissions, role_permissions, user_roles
from app.models.department import Department
from app.models.menu import Menu
from app.models.permission import Permission
from app.models.role import Role
from app.models.system_config import SystemConfig
from app.models.user import User


async def seed(db: AsyncSession) -> None:
    # --- Check if already seeded ---
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none() is not None:
        print("数据库已有数据，跳过种子初始化。")
        return

    # ============================================================
    # 1. Create Default Department
    # ============================================================
    dept = Department(name="总公司", sort_order=1, status=True)
    db.add(dept)
    await db.flush()
    print(f"✅ 创建默认部门: {dept.name} (id={dept.id})")

    # ============================================================
    # 2. Create Permissions
    # ============================================================
    permissions_data = [
        # Dashboard
        {"name": "仪表盘", "code": "dashboard", "type": "MENU", "sort_order": 1},
        {"name": "仪表盘访问", "code": "dashboard:view", "type": "BUTTON", "sort_order": 1},
        # User Management
        {"name": "用户管理", "code": "system:user", "type": "MENU", "sort_order": 10},
        {"name": "用户列表", "code": "system:user:list", "type": "BUTTON", "sort_order": 1},
        {"name": "创建用户", "code": "system:user:create", "type": "BUTTON", "sort_order": 2},
        {"name": "编辑用户", "code": "system:user:update", "type": "BUTTON", "sort_order": 3},
        {"name": "删除用户", "code": "system:user:delete", "type": "BUTTON", "sort_order": 4},
        # Department Management
        {"name": "部门管理", "code": "system:department", "type": "MENU", "sort_order": 20},
        {"name": "部门列表", "code": "system:department:list", "type": "BUTTON", "sort_order": 1},
        {"name": "创建部门", "code": "system:department:create", "type": "BUTTON", "sort_order": 2},
        {"name": "编辑部门", "code": "system:department:update", "type": "BUTTON", "sort_order": 3},
        {"name": "删除部门", "code": "system:department:delete", "type": "BUTTON", "sort_order": 4},
        # Role Management
        {"name": "角色管理", "code": "system:role", "type": "MENU", "sort_order": 30},
        {"name": "角色列表", "code": "system:role:list", "type": "BUTTON", "sort_order": 1},
        {"name": "创建角色", "code": "system:role:create", "type": "BUTTON", "sort_order": 2},
        {"name": "编辑角色", "code": "system:role:update", "type": "BUTTON", "sort_order": 3},
        {"name": "删除角色", "code": "system:role:delete", "type": "BUTTON", "sort_order": 4},
        # Permission Management
        {"name": "权限管理", "code": "system:permission", "type": "MENU", "sort_order": 40},
        {"name": "权限列表", "code": "system:permission:list", "type": "BUTTON", "sort_order": 1},
        {"name": "创建权限", "code": "system:permission:create", "type": "BUTTON", "sort_order": 2},
        {"name": "编辑权限", "code": "system:permission:update", "type": "BUTTON", "sort_order": 3},
        {"name": "删除权限", "code": "system:permission:delete", "type": "BUTTON", "sort_order": 4},
        # Menu Management
        {"name": "菜单管理", "code": "system:menu", "type": "MENU", "sort_order": 50},
        {"name": "菜单列表", "code": "system:menu:list", "type": "BUTTON", "sort_order": 1},
        {"name": "创建菜单", "code": "system:menu:create", "type": "BUTTON", "sort_order": 2},
        {"name": "编辑菜单", "code": "system:menu:update", "type": "BUTTON", "sort_order": 3},
        {"name": "删除菜单", "code": "system:menu:delete", "type": "BUTTON", "sort_order": 4},
        # System Config
        {"name": "系统配置", "code": "system:config", "type": "MENU", "sort_order": 60},
        {"name": "配置列表", "code": "system:config:list", "type": "BUTTON", "sort_order": 1},
        {"name": "编辑配置", "code": "system:config:update", "type": "BUTTON", "sort_order": 2},
        # Operation Log
        {
            "name": "操作日志", "code": "system:operation_log",
            "type": "MENU", "sort_order": 70,
        },
        {
            "name": "日志列表", "code": "system:operation_log:list",
            "type": "BUTTON", "sort_order": 1,
        },
    ]

    perm_map: dict[str, Permission] = {}
    for p in permissions_data:
        perm = Permission(
            name=p["name"],
            code=p["code"],
            type=p["type"],
            sort_order=p.get("sort_order", 0),
            status=True,
        )
        db.add(perm)
        await db.flush()
        perm_map[p["code"]] = perm

    # Set parent-child relationships for permissions
    parent_map = {
        "dashboard:view": "dashboard",
        "system:user:list": "system:user",
        "system:user:create": "system:user",
        "system:user:update": "system:user",
        "system:user:delete": "system:user",
        "system:department:list": "system:department",
        "system:department:create": "system:department",
        "system:department:update": "system:department",
        "system:department:delete": "system:department",
        "system:role:list": "system:role",
        "system:role:create": "system:role",
        "system:role:update": "system:role",
        "system:role:delete": "system:role",
        "system:permission:list": "system:permission",
        "system:permission:create": "system:permission",
        "system:permission:update": "system:permission",
        "system:permission:delete": "system:permission",
        "system:menu:list": "system:menu",
        "system:menu:create": "system:menu",
        "system:menu:update": "system:menu",
        "system:menu:delete": "system:menu",
        "system:config:list": "system:config",
        "system:config:update": "system:config",
        "system:operation_log:list": "system:operation_log",
    }
    for child_code, parent_code in parent_map.items():
        if child_code in perm_map and parent_code in perm_map:
            perm_map[child_code].parent_id = perm_map[parent_code].id

    await db.flush()
    print(f"✅ 创建权限: {len(permissions_data)} 条")

    # ============================================================
    # 3. Create Menus and Bind Permissions
    # ============================================================
    menus_data = [
        {
            "name": "系统管理", "icon": "SettingOutlined",
            "route_path": "/system", "sort_order": 10, "hidden": False,
        },
        {
            "name": "用户管理", "icon": "UserOutlined",
            "route_path": "/system/user", "component": "system/user/index",
            "parent": "系统管理", "sort_order": 1, "perm_code": "system:user",
        },
        {
            "name": "部门管理", "icon": "ApartmentOutlined",
            "route_path": "/system/department", "component": "system/department/index",
            "parent": "系统管理", "sort_order": 2, "perm_code": "system:department",
        },
        {
            "name": "角色管理", "icon": "TeamOutlined",
            "route_path": "/system/role", "component": "system/role/index",
            "parent": "系统管理", "sort_order": 3, "perm_code": "system:role",
        },
        {
            "name": "权限管理", "icon": "SafetyOutlined",
            "route_path": "/system/permission", "component": "system/permission/index",
            "parent": "系统管理", "sort_order": 4, "perm_code": "system:permission",
        },
        {
            "name": "菜单管理", "icon": "MenuOutlined",
            "route_path": "/system/menu", "component": "system/menu/index",
            "parent": "系统管理", "sort_order": 5, "perm_code": "system:menu",
        },
        {
            "name": "系统配置", "icon": "SettingOutlined",
            "route_path": "/system/config", "component": "system/config/index",
            "parent": "系统管理", "sort_order": 6, "perm_code": "system:config",
        },
        {
            "name": "操作日志", "icon": "FileTextOutlined",
            "route_path": "/system/log", "component": "system/log/index",
            "parent": "系统管理", "sort_order": 7, "perm_code": "system:operation_log",
        },
    ]

    menu_map: dict[str, Menu] = {}
    for m in menus_data:
        menu = Menu(
            name=m["name"],
            icon=m.get("icon"),
            route_path=m["route_path"],
            component=m.get("component"),
            hidden=m.get("hidden", False),
            is_external_link=False,
            sort_order=m["sort_order"],
            status=True,
        )
        if m.get("parent"):
            parent_menu = menu_map.get(m["parent"])
            if parent_menu:
                menu.parent_id = parent_menu.id
        db.add(menu)
        await db.flush()
        menu_map[m["name"]] = menu

        if m.get("perm_code") and m["perm_code"] in perm_map:
            perm_id = perm_map[m["perm_code"]].id
            await db.execute(
                menu_permissions.insert().values(menu_id=menu.id, permission_id=perm_id)
            )

    await db.flush()
    print(f"✅ 创建菜单: {len(menus_data)} 条")

    # ============================================================
    # 4. Create Admin Role
    # ============================================================
    admin_role = Role(
        name="超级管理员", code="admin", status=True,
        remark="系统超级管理员，拥有所有权限",
    )
    db.add(admin_role)
    await db.flush()
    for perm in perm_map.values():
        await db.execute(
            role_permissions.insert().values(role_id=admin_role.id, permission_id=perm.id)
        )
    print(f"✅ 创建角色: {admin_role.name} (id={admin_role.id})")

    # ============================================================
    # 5. Create Admin User
    # ============================================================
    admin_user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("admin"),
        status=True,
        is_superuser=True,
        department_id=dept.id,
    )
    db.add(admin_user)
    await db.flush()
    await db.execute(
        user_roles.insert().values(user_id=admin_user.id, role_id=admin_role.id)
    )
    print("✅ 创建超级管理员: admin (密码: admin, is_superuser=True)")

    # ============================================================
    # 6. Create System Configs
    # ============================================================
    configs_data = [
        {
            "group": "basic", "key": "site_name", "value": "AI Admin",
            "value_type": "STRING", "sort_order": 1, "remark": "站点名称",
        },
        {
            "group": "basic", "key": "logo", "value": "",
            "value_type": "STRING", "sort_order": 2, "remark": "站点 Logo URL",
        },
        {
            "group": "security", "key": "default_password", "value": "123456",
            "value_type": "STRING", "sort_order": 1, "remark": "新用户默认密码",
        },
        {
            "group": "security", "key": "password_min_length", "value": "6",
            "value_type": "INTEGER", "sort_order": 2, "remark": "密码最小长度",
        },
        {
            "group": "security", "key": "max_login_attempts", "value": "5",
            "value_type": "INTEGER", "sort_order": 3, "remark": "最大登录尝试次数",
        },
        {
            "group": "log", "key": "log_retention_days", "value": "90",
            "value_type": "INTEGER", "sort_order": 1, "remark": "操作日志保留天数",
        },
    ]
    for c in configs_data:
        config = SystemConfig(**c)
        db.add(config)
    await db.flush()
    print(f"✅ 创建系统配置: {len(configs_data)} 条")

    # ============================================================
    # Commit
    # ============================================================
    await db.commit()
    print("=" * 50)
    print("🎉 数据库初始化完成！")
    print("   管理员账号: admin / admin")
    print(f"   已创建: 1 个部门, {len(permissions_data)} 个权限, ", end="")
    print(f"{len(menus_data)} 个菜单, 1 个角色, {len(configs_data)} 个配置")


async def main() -> None:
    async with async_session() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
