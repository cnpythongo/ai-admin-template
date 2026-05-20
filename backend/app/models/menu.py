from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModelMixin

if TYPE_CHECKING:
    from app.models.permission import Permission


class Menu(BaseModelMixin, Base):
    __tablename__ = "menus"

    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="菜单名称"
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("menus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="上级菜单ID",
    )
    route_path: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="路由路径"
    )
    component: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="组件路径"
    )
    icon: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="图标"
    )
    hidden: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否隐藏"
    )
    is_external_link: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否外链"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="状态"
    )

    # Self-referential relationships
    children: Mapped[list[Menu]] = relationship(
        "Menu",
        back_populates="parent",
        cascade="all",
        lazy="selectin",
    )
    parent: Mapped[Menu | None] = relationship(
        "Menu",
        back_populates="children",
        remote_side="Menu.id",
        lazy="selectin",
    )

    # Many-to-many with Permission
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary="menu_permissions",
        backref="menus",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Menu(id={self.id}, name='{self.name}')>"

