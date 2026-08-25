from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[Any], total: int, page: int, size: int) -> "PaginatedResponse[Any]":
        pages = max(1, (total + size - 1) // size)
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class StatusResponse(BaseModel):
    """Simple status/message response."""

    success: bool = True
    message: str
