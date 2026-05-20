from __future__ import annotations

import base64
import json
import logging
from typing import Any

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.system_config import ConfigValueType, SystemConfig
from app.schemas.system_config import ConfigGroupResponse, SystemConfigResponse

logger = logging.getLogger(__name__)

CACHE_PREFIX = "config:"

# Maximum page size for batch operations
_BATCH_SIZE = 100


def _get_fernet() -> Fernet:
    """Derive a Fernet cipher instance from the application SECRET_KEY."""
    # Fernet requires a 32-byte URL-safe base64 key
    key_bytes = settings.SECRET_KEY.encode("utf-8")
    # Pad/truncate to 32 bytes using SHA256
    import hashlib

    digest = hashlib.sha256(key_bytes).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)


def _encrypt_value(plain_value: str) -> str:
    """Encrypt a sensitive configuration value."""
    fernet = _get_fernet()
    return fernet.encrypt(plain_value.encode("utf-8")).decode("utf-8")


def _decrypt_value(encrypted_value: str) -> str:
    """Decrypt a sensitive configuration value."""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")


def _validate_value(value: Any, value_type: ConfigValueType) -> str:
    """Validate and convert the value based on its type.

    Args:
        value: The raw value input (may be string or native type).
        value_type: The expected configuration value type.

    Returns:
        The validated value as a string for DB storage.

    Raises:
        HTTPException 400 if validation fails.
    """
    try:
        if value_type == ConfigValueType.INTEGER:
            # Accept int, float, or string representation
            int_value = int(str(value))
            return str(int_value)
        elif value_type == ConfigValueType.BOOLEAN:
            if isinstance(value, bool):
                return str(value).lower()
            if isinstance(value, str):
                lower = value.strip().lower()
                if lower in ("true", "1", "yes"):
                    return "true"
                elif lower in ("false", "0", "no"):
                    return "false"
                else:
                    raise ValueError(f"Cannot interpret '{value}' as boolean")
            if isinstance(value, int):
                return "true" if value else "false"
            raise ValueError(f"Cannot interpret '{value}' as boolean")
        elif value_type == ConfigValueType.JSON:
            if isinstance(value, str):
                # Try to parse to validate
                parsed = json.loads(value)
                return json.dumps(parsed, ensure_ascii=False)
            # If it's already a dict/list, serialize it
            return json.dumps(value, ensure_ascii=False)
        elif value_type == ConfigValueType.SELECT:
            return str(value)
        else:  # STRING
            return str(value)
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Value validation failed for type '{value_type}': {e}",
        )


class SystemConfigService:
    """Service for system configuration management.

    Handles CRUD operations with Redis caching and sensitive value encryption.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
    ) -> None:
        self.db = db
        self.redis = redis

    async def get_groups(self) -> list[ConfigGroupResponse]:
        """Get all distinct configuration groups.

        Returns:
            List of ConfigGroupResponse with name and code.
        """
        result = await self.db.execute(
            select(SystemConfig.group).distinct().order_by(SystemConfig.group)
        )
        groups = result.scalars().all()
        return [ConfigGroupResponse(name=group, code=group) for group in groups]

    async def get_by_group(self, group: str) -> list[SystemConfigResponse]:
        """Get all configurations in a group.

        Reads from Redis cache first (key: ``config:{key}``),
        falls back to DB on cache miss. Sensitive values are masked.

        Args:
            group: The configuration group code.

        Returns:
            List of SystemConfigResponse sorted by sort_order.
        """
        result = await self.db.execute(
            select(SystemConfig)
            .where(SystemConfig.group == group)
            .order_by(SystemConfig.sort_order, SystemConfig.id)
        )
        configs = result.scalars().all()

        responses: list[SystemConfigResponse] = []
        for config in configs:
            # Try cache first
            cache_key = f"{CACHE_PREFIX}{config.key}"
            cached_value = await self.redis.get(cache_key)

            if cached_value is not None:
                value = cached_value
            else:
                value = config.value
                # Populate cache
                await self.redis.setex(cache_key, 3600, value)

            # Mask sensitive values
            if config.is_sensitive:
                value = "******"

            responses.append(
                SystemConfigResponse(
                    id=config.id,
                    group=config.group,
                    key=config.key,
                    value=value,
                    value_type=config.value_type,
                    is_sensitive=config.is_sensitive,
                    sort_order=config.sort_order,
                    remark=config.remark,
                    created_at=config.created_at,
                    updated_at=config.updated_at,
                )
            )

        return responses

    async def update(
        self,
        config_id: int,
        value: Any,
        is_superuser: bool,
    ) -> SystemConfigResponse:
        """Update a configuration value.

        Args:
            config_id: The ID of the configuration to update.
            value: The new value for the configuration.
            is_superuser: Whether the requesting user is a superuser.
                Required to update sensitive configurations.

        Returns:
            The updated SystemConfigResponse.

        Raises:
            HTTPException 404 if config not found.
            HTTPException 403 if updating sensitive config without superuser.
            HTTPException 400 if value validation fails.
        """
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.id == config_id))
        config = result.scalar_one_or_none()

        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration not found",
            )

        # Sensitive configs require superuser
        if config.is_sensitive and not is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can update sensitive configurations",
            )

        # Validate and convert value
        validated_value = _validate_value(value, config.value_type)

        # Encrypt if sensitive
        if config.is_sensitive:
            validated_value = _encrypt_value(validated_value)

        config.value = validated_value
        await self.db.flush()

        # Invalidate cache
        cache_key = f"{CACHE_PREFIX}{config.key}"
        await self.redis.delete(cache_key)

        logger.info("Config updated: key=%s, group=%s", config.key, config.group)

        return SystemConfigResponse(
            id=config.id,
            group=config.group,
            key=config.key,
            value=str(value) if not config.is_sensitive else "******",
            value_type=config.value_type,
            is_sensitive=config.is_sensitive,
            sort_order=config.sort_order,
            remark=config.remark,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    async def refresh_cache(self) -> int:
        """Refresh all configuration values in Redis cache.

        Loads all configs from DB and writes each to Redis
        (key: ``config:{key}``). Sensitive values are decrypted
        before caching so the cache holds the plain value.

        Returns:
            The number of configurations cached.
        """
        result = await self.db.execute(select(SystemConfig).order_by(SystemConfig.id))
        configs = result.scalars().all()

        count = 0
        for config in configs:
            cache_key = f"{CACHE_PREFIX}{config.key}"
            value = config.value

            # Decrypt sensitive values before caching
            if config.is_sensitive:
                try:
                    value = _decrypt_value(value)
                except Exception:
                    logger.warning(
                        "Failed to decrypt config key=%s, caching encrypted value",
                        config.key,
                    )

            await self.redis.setex(cache_key, 3600, value)
            count += 1

        logger.info("Config cache refreshed: %d entries cached", count)
        return count


async def get_system_config_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SystemConfigService:
    """Dependency provider for SystemConfigService."""
    return SystemConfigService(db=db, redis=redis)
