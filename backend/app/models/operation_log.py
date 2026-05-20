from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="操作用户ID",
    )
    username: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="操作用户名"
    )
    module: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="操作模块"
    )
    action: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="操作类型"
    )
    target_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="操作目标ID"
    )
    target_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="操作目标名称"
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="请求IP"
    )
    request_method: Mapped[str | None] = mapped_column(
        String(16), nullable=True, comment="请求方法"
    )
    request_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="请求路径"
    )
    request_params: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="请求参数 (JSON)"
    )
    status: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="操作结果: 1=成功 0=失败"
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="耗时(毫秒)"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="错误信息"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="操作时间",
    )

    def __repr__(self) -> str:
        return f"<OperationLog(id={self.id}, module='{self.module}', action='{self.action}')>"
