from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.operation_log_service import cleanup_old_logs, flush_logs

logger = logging.getLogger(__name__)

FLUSH_INTERVAL = 5  # seconds
CLEANUP_INTERVAL = 3600  # 1 hour


async def run_log_processor(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Background task that periodically flushes logs from Redis to DB.

    Also triggers old log cleanup once per CLEANUP_INTERVAL.
    """
    logger.info("Log processor started")
    cleanup_counter = 0

    while True:
        try:
            async with session_factory() as db:
                count = await flush_logs(db)
                if count > 0:
                    logger.debug("Flushed %d log entries to database", count)
        except Exception:
            logger.exception("Error flushing logs")

        cleanup_counter += FLUSH_INTERVAL
        if cleanup_counter >= CLEANUP_INTERVAL:
            try:
                async with session_factory() as db:
                    deleted = await cleanup_old_logs(db)
                    if deleted > 0:
                        logger.info("Cleaned up %d old log entries", deleted)
            except Exception:
                logger.exception("Error cleaning up old logs")
            cleanup_counter = 0

        await asyncio.sleep(FLUSH_INTERVAL)
