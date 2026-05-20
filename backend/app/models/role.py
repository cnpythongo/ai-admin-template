from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModelMixin

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.user import User


class Role(BaseModelMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="角色名称"
    )
    code: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="角色编码",
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="状态"
    )
    remark: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="备注"
    )

    # Many-to-many with Permission
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary="role_permissions",
        backref="roles",
        lazy="selectin",
    )

    # Many-to-many with User
    users: Mapped[list[User]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', code='{self.code}')>"
