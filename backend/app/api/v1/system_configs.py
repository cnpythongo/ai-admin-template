from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.core.permission import require_permissions
from app.models.user import User
from app.schemas.common import success
from app.schemas.system_config import SystemConfigUpdate
from app.services.system_config_service import (
    SystemConfigService,
    get_system_config_service,
)

router = APIRouter(prefix="/system-configs", tags=["系统配置"])


@router.get("/groups", summary="获取配置分组列表")
async def get_config_groups(
    _: Annotated[None, Depends(require_permissions("system:config:list"))],
    service: SystemConfigService = Depends(get_system_config_service),
):
    """Get all distinct configuration groups."""
    groups = await service.get_groups()
    return success(data=groups)


@router.get("", summary="获取配置列表（按分组）")
async def get_configs_by_group(
    _: Annotated[None, Depends(require_permissions("system:config:list"))],
    group: str = Query(..., description="Configuration group code"),
    service: SystemConfigService = Depends(get_system_config_service),
):
    """Get all configurations in a specified group."""
    configs = await service.get_by_group(group)
    return success(data=configs)


@router.put("/{config_id}", summary="更新配置值")
async def update_config(
    _: Annotated[None, Depends(require_permissions("system:config:update"))],
    config_id: int,
    request: SystemConfigUpdate,
    current_user: User = Depends(get_current_user),
    service: SystemConfigService = Depends(get_system_config_service),
):
    """Update a configuration value.

    Sensitive configurations can only be updated by superusers.
    The value is validated based on the configuration's value_type.
    """
    config = await service.update(
        config_id=config_id,
        value=request.value,
        is_superuser=current_user.is_superuser,
    )
    return success(data=config)


@router.post("/refresh-cache", summary="刷新配置缓存")
async def refresh_config_cache(
    _: Annotated[None, Depends(require_permissions("system:config:update"))],
    service: SystemConfigService = Depends(get_system_config_service),
):
    """Manually refresh all configuration values in Redis cache."""
    count = await service.refresh_cache()
    return success(data={"count": count}, message=f"已刷新 {count} 条配置缓存")
