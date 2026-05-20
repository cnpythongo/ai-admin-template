"""SQLAlchemy models and association tables.

All models are imported here so Alembic can auto-discover them.
Association tables are defined here to avoid circular imports.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Table

from app.models.base import Base

# Association table: user <-> role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "user_id",
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "role_id",
        BigInteger,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
)

# Association table: role <-> permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "role_id",
        BigInteger,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "permission_id",
        BigInteger,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
)

# Association table: menu <-> permission
menu_permissions = Table(
    "menu_permissions",
    Base.metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "menu_id",
        BigInteger,
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "permission_id",
        BigInteger,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
)

# Import all models so Alembic can discover them
from app.models.department import Department  # noqa: E402, F401
from app.models.menu import Menu  # noqa: E402, F401
from app.models.operation_log import OperationLog  # noqa: E402, F401
from app.models.permission import Permission  # noqa: E402, F401
from app.models.role import Role  # noqa: E402, F401
from app.models.system_config import SystemConfig  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401

__all__ = [
    "Base",
    "Department",
    "Menu",
    "OperationLog",
    "Permission",
    "Role",
    "SystemConfig",
    "User",
    "user_roles",
    "role_permissions",
    "menu_permissions",
]
