from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModelMixin


class Department(BaseModelMixin, Base):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="部门名称")
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="上级部门ID",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="状态: True=启用 False=禁用"
    )

    # Self-referential relationships
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
        cascade="all",
        lazy="selectin",
    )
    parent: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="children",
        remote_side="Department.id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}')>"


