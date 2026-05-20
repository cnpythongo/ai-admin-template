from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseModelMixin


class ConfigValueType(enum.StrEnum):
    """配置值类型"""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    JSON = "json"
    SELECT = "select"


class SystemConfig(BaseModelMixin, Base):
    __tablename__ = "system_configs"

    group: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True, comment="配置分组"
    )
    key: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="配置键",
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False, comment="配置值"
    )
    value_type: Mapped[ConfigValueType] = mapped_column(
        Enum(ConfigValueType, length=16),
        nullable=False,
        default=ConfigValueType.STRING,
        comment="值类型",
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否敏感字段"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序"
    )
    remark: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="备注"
    )

    def __repr__(self) -> str:
        return f"<SystemConfig(id={self.id}, key='{self.key}')>"
