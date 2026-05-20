from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.system_config import ConfigValueType


class ConfigGroupResponse(BaseModel):
    """Configuration group listing response."""

    name: str
    code: str


class SystemConfigCreate(BaseModel):
    """Schema for creating a new system configuration."""

    group: str = Field(..., description="Configuration group code")
    key: str = Field(..., description="Unique configuration key")
    value: str = Field(..., description="Configuration value")
    value_type: ConfigValueType = Field(default=ConfigValueType.STRING, description="Value type")
    is_sensitive: bool = Field(default=False, description="Whether the value is sensitive")
    sort_order: int = Field(default=0, description="Sort order")
    remark: str | None = Field(default=None, description="Remark")


class SystemConfigUpdate(BaseModel):
    """Schema for updating a configuration value."""

    value: Any = Field(..., description="New configuration value")


class SystemConfigResponse(BaseModel):
    """Schema for system configuration response."""

    id: int
    group: str
    key: str
    value: str | None
    value_type: ConfigValueType
    is_sensitive: bool
    sort_order: int
    remark: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
