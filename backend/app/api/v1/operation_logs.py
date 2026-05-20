from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permission import require_permissions
from app.db.session import get_db
from app.schemas.common import PaginatedData, success
from app.services import operation_log_service

router = APIRouter(prefix="/operation-logs", tags=["操作日志"])


@router.get("", summary="分页查询操作日志")
async def list_operation_logs(
    _: Annotated[None, Depends(require_permissions("system:operation_log:list"))],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    username: str | None = Query(None, description="操作用户名"),
    module: str | None = Query(None, description="操作模块"),
    action: str | None = Query(None, description="操作类型"),
    status: int | None = Query(None, description="操作结果: 1=成功 0=失败"),
    start_time: str | None = Query(None, description="开始时间"),
    end_time: str | None = Query(None, description="结束时间"),
):
    """Get paginated list of operation logs with multi-condition filters."""
    items, total = await operation_log_service.get_list(
        db,
        page=page,
        page_size=page_size,
        username=username,
        module=module,
        action=action,
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    return success(
        data=PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/modules", summary="获取操作模块列表")
async def list_modules(
    _: Annotated[None, Depends(require_permissions("system:operation_log:list"))],
    db: AsyncSession = Depends(get_db),
):
    """Get distinct module names from operation logs."""
    from sqlalchemy import select

    from app.models.operation_log import OperationLog

    result = await db.execute(select(OperationLog.module).distinct())
    modules = [row[0] for row in result.fetchall() if row[0]]
    return success(data=modules)


@router.get("/actions", summary="获取操作类型列表")
async def list_actions(
    _: Annotated[None, Depends(require_permissions("system:operation_log:list"))],
    db: AsyncSession = Depends(get_db),
    module: str | None = Query(None, description="按模块筛选"),
):
    """Get distinct action names, optionally filtered by module."""
    from sqlalchemy import select

    from app.models.operation_log import OperationLog

    query = select(OperationLog.action).distinct()
    if module:
        query = query.where(OperationLog.module == module)
    result = await db.execute(query)
    actions = [row[0] for row in result.fetchall() if row[0]]
    return success(data=actions)


@router.get("/{log_id}", summary="获取日志详情")
async def get_operation_log(
    log_id: int,
    _: Annotated[None, Depends(require_permissions("system:operation_log:list"))],
    db: AsyncSession = Depends(get_db),
):
    """Get full detail of a single operation log."""
    detail = await operation_log_service.get_detail(db, log_id)
    return success(data=detail)
