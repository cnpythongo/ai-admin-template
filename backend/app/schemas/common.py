from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):  # noqa: UP046
    """Unified API response format.

    code: 0 for success, non-zero for errors
    data: response payload, null on error
    message: "ok" on success, error description on failure
    """

    code: int = 0
    data: DataT | None = None
    message: str = "ok"


class PaginatedData(BaseModel, Generic[DataT]):  # noqa: UP046
    """Paginated response wrapper."""

    items: list[DataT]
    total: int
    page: int = 1
    page_size: int = 10


def success(*, data: Any = None, message: str = "ok") -> ApiResponse:
    """Return a success response."""
    return ApiResponse(code=0, data=data, message=message)


def error(*, code: int = 40001, message: str = "error", data: Any = None) -> ApiResponse:
    """Return an error response."""
    return ApiResponse(code=code, data=data, message=message)
