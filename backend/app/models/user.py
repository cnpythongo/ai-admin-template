from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModelMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.role import Role


class User(BaseModelMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名",
    )
    password_hash: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="密码哈希"
    )
    nickname: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="昵称"
    )
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="邮箱"
    )
    phone: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="手机号"
    )
    avatar: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="头像URL"
    )
    department_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="部门ID",
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="状态: True=启用 False=禁用"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否超级管理员"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否逻辑删除"
    )

    # Relationships
    department: Mapped[Department | None] = relationship(
        "Department",
        backref="users",
        lazy="selectin",
    )
    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"

