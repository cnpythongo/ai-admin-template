from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token
from app.db.redis import redis_pool
from app.services.log_queue import enqueue_log

logger = logging.getLogger(__name__)

PATH_MODULE_MAP: dict[str, str] = {
    "/api/v1/auth": "auth",
    "/api/v1/users": "user",
    "/api/v1/departments": "department",
    "/api/v1/roles": "role",
    "/api/v1/permissions": "permission",
    "/api/v1/menus": "menu",
    "/api/v1/system-configs": "system_config",
    "/api/v1/operation-logs": "operation_log",
}

SPECIAL_ROUTES: dict[str, tuple[str, str]] = {
    "/api/v1/auth/login": ("auth", "login"),
    "/api/v1/auth/refresh": ("auth", "refresh"),
    "/api/v1/auth/password": ("auth", "update"),
}

ACTION_MAP: dict[str, str] = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _get_module(path: str) -> str:
    for prefix, module in PATH_MODULE_MAP.items():
        if path.startswith(prefix):
            return module
    return "other"


def _get_action(path: str, method: str) -> str:
    if path in SPECIAL_ROUTES:
        return SPECIAL_ROUTES[path][1]
    return ACTION_MAP.get(method, "other")


def _extract_target_id(path: str, method: str) -> str | None:
    parts = path.rstrip("/").split("/")
    for part in reversed(parts):
        if part.isdigit():
            return part
    return None


def _get_user_info_from_token(request: Request) -> tuple[int | None, str | None]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, None
    token = auth_header.removeprefix("Bearer ")
    payload = decode_token(token)
    if payload is None:
        return None, None
    sub = payload.get("sub")
    user_id = None
    if sub is not None:
        try:
            user_id = int(sub)
        except (ValueError, TypeError):
            pass
    username = payload.get("username")
    return user_id, username


def _extract_id_from_body(body: bytes) -> str | None:
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            return None
        payload = data.get("data")
        if isinstance(payload, dict):
            raw_id = payload.get("id")
            if raw_id is not None:
                return str(raw_id)
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return None


async def _capture_response_body(response: Response) -> tuple[Response, bytes]:
    body = b""
    try:
        body = response.body
    except AttributeError:
        chunks = [chunk async for chunk in response.body_iterator]
        body = b"".join(chunks)
        response = Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
    return response, body


class OperationLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if not path.startswith("/api/v1/"):
            return await call_next(request)

        if path in ("/api/v1/operation-logs",):
            return await call_next(request)

        method = request.method
        is_write = method in WRITE_METHODS

        if is_write:
            start_time = time.time()
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            response, body = await _capture_response_body(response)

            module = _get_module(path)
            action = _get_action(path, method)
            target_id = _extract_target_id(path, method)

            if target_id is None and method == "POST" and response.status_code < 400:
                target_id = _extract_id_from_body(body)

            user_id, username = _get_user_info_from_token(request)
            ip_address = request.client.host if request.client else None

            log_data = {
                "user_id": user_id,
                "username": username,
                "module": module,
                "action": action,
                "target_id": target_id,
                "target_name": target_id,
                "ip_address": ip_address,
                "request_method": method,
                "request_path": path,
                "request_params": None,
                "status": 1 if response.status_code < 400 else 0,
                "duration_ms": duration_ms,
                "error_message": None,
            }

            try:
                r = Redis(connection_pool=redis_pool)
                await enqueue_log(r, log_data)
                await r.close()
            except Exception:
                logger.exception("Failed to enqueue operation log")

            return response

        return await call_next(request)
