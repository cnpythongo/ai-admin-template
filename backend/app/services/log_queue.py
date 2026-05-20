from __future__ import annotations

import json

from redis.asyncio import Redis

LOG_QUEUE_KEY = "log_queue"


async def enqueue_log(redis: Redis, log_data: dict) -> None:
    """Push a log entry to the Redis queue."""
    await redis.lpush(LOG_QUEUE_KEY, json.dumps(log_data, default=str))  # type: ignore[misc]


async def dequeue_batch(redis: Redis, batch_size: int = 100) -> list[dict]:
    """Pop a batch of log entries from the Redis queue."""
    logs: list[dict] = []
    for _ in range(batch_size):
        data = await redis.rpop(LOG_QUEUE_KEY)  # type: ignore[misc]
        if data is None:
            break
        try:
            logs.append(json.loads(data))
        except (json.JSONDecodeError, TypeError):
            continue
    return logs


async def get_queue_length(redis: Redis) -> int:
    """Get the current number of pending log entries."""
    return await redis.llen(LOG_QUEUE_KEY)  # type: ignore[no-any-return,misc]
