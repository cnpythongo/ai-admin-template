from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModelMixin


class PermissionType(enum.StrEnum):
    """权限类型: menu=菜单, button=按钮, api=API接口"""

    MENU = "menu"
    BUTTON = "button"
    API = "api"


class Permission(BaseModelMixin, Base):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="权限名称"
    )
    code: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="权限编码 (格式: module:sub:action)",
    )
    type: Mapped[PermissionType] = mapped_column(
        Enum(PermissionType, length=16),
        nullable=False,
        comment="权限类型: menu/button/api",
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("permissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="上级权限ID",
    )
    api_path: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="API路径 (type=api时必填)"
    )
    api_method: Mapped[str | None] = mapped_column(
        String(16), nullable=True, comment="HTTP方法 (type=api时必填)"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="状态"
    )
    remark: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="备注"
    )

    # Self-referential relationships
    children: Mapped[list[Permission]] = relationship(
        "Permission",
        back_populates="parent",
        cascade="all",
        lazy="selectin",
    )
    parent: Mapped[Permission | None] = relationship(
        "Permission",
        back_populates="children",
        remote_side="Permission.id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code='{self.code}', type='{self.type}')>"

