from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OperationLogResponse(BaseModel):
    """Schema for operation log response."""

    id: int
    user_id: int | None
    username: str | None
    module: str
    action: str
    target_id: str | None
    target_name: str | None
    ip_address: str | None
    request_method: str | None
    request_path: str | None
    status: int
    duration_ms: int | None
    error_message: str | None
    created_at: datetime


class OperationLogQuery(BaseModel):
    """Schema for operation log query parameters."""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页条数")
    username: str | None = Field(default=None, description="操作用户名")
    module: str | None = Field(default=None, description="操作模块")
    action: str | None = Field(default=None, description="操作类型")
    status: int | None = Field(default=None, description="操作结果: 1=成功 0=失败")
    start_time: str | None = Field(default=None, description="开始时间")
    end_time: str | None = Field(default=None, description="结束时间")
