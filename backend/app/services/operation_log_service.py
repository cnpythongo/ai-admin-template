from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation_log import OperationLog
from app.services.log_queue import dequeue_batch

logger = logging.getLogger(__name__)

LOG_RETENTION_DAYS = 90
BATCH_SIZE = 100
FLUSH_INTERVAL = 5  # seconds


async def flush_logs(db: AsyncSession) -> int:
    """Flush pending logs from Redis queue to database.

    Returns the number of logs flushed.
    """
    from redis.asyncio import Redis

    from app.db.redis import redis_pool

    r = Redis(connection_pool=redis_pool)
    try:
        batch = await dequeue_batch(r, BATCH_SIZE)
        if not batch:
            return 0

        logs = [
            OperationLog(
                user_id=entry.get("user_id"),
                username=entry.get("username"),
                module=entry.get("module", ""),
                action=entry.get("action", ""),
                target_id=entry.get("target_id"),
                target_name=entry.get("target_name"),
                ip_address=entry.get("ip_address"),
                request_method=entry.get("request_method"),
                request_path=entry.get("request_path"),
                request_params=entry.get("request_params"),
                status=entry.get("status", 1),
                duration_ms=entry.get("duration_ms"),
                error_message=entry.get("error_message"),
                created_at=datetime.now(UTC),
            )
            for entry in batch
        ]
        db.add_all(logs)
        await db.commit()
        return len(logs)
    finally:
        await r.close()


async def cleanup_old_logs(db: AsyncSession) -> int:
    """Delete operation logs older than the retention period.

    Returns the number of deleted logs.
    """
    cutoff = datetime.now(UTC) - timedelta(days=LOG_RETENTION_DAYS)
    result = await db.execute(
        select(OperationLog).where(OperationLog.created_at < cutoff)
    )
    old_logs: Sequence[OperationLog] = result.scalars().all()
    count = len(old_logs)
    for log in old_logs:
        await db.delete(log)
    await db.commit()
    return count


async def get_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    username: str | None = None,
    module: str | None = None,
    action: str | None = None,
    status: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> tuple[list[dict], int]:
    """Get paginated list of operation logs with filters."""
    base_query = select(OperationLog)

    if username is not None:
        base_query = base_query.where(OperationLog.username.ilike(f"%{username}%"))
    if module is not None:
        base_query = base_query.where(OperationLog.module == module)
    if action is not None:
        base_query = base_query.where(OperationLog.action == action)
    if status is not None:
        base_query = base_query.where(OperationLog.status == status)
    if start_time is not None:
        base_query = base_query.where(OperationLog.created_at >= start_time)
    if end_time is not None:
        base_query = base_query.where(OperationLog.created_at <= end_time)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Query paginated logs
    offset_val = (page - 1) * page_size
    query = base_query.order_by(OperationLog.id.desc()).offset(offset_val).limit(page_size)
    result = await db.execute(query)
    logs: Sequence[OperationLog] = result.scalars().all()

    items = [_log_to_dict(log) for log in logs]
    return items, total


def _log_to_dict(log: OperationLog) -> dict:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.username,
        "module": log.module,
        "action": log.action,
        "target_id": log.target_id,
        "target_name": log.target_name,
        "ip_address": log.ip_address,
        "request_method": log.request_method,
        "request_path": log.request_path,
        "request_params": log.request_params,
        "status": log.status,
        "duration_ms": log.duration_ms,
        "error_message": log.error_message,
        "created_at": log.created_at,
    }


async def get_detail(db: AsyncSession, log_id: int) -> dict:
    """Get a single operation log by id with full detail (including request_params)."""
    result = await db.execute(
        select(OperationLog).where(OperationLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="操作日志不存在",
        )
    return _log_to_dict(log)
