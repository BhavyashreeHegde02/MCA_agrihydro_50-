"""Shared response shapes."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """The single error shape every failure uses.

    One consistent envelope means the Flutter client writes one error handler
    rather than one per endpoint.
    """

    error: str = Field(description="Stable machine-readable code")
    message: str = Field(description="Human-readable explanation")
    details: dict[str, Any] | None = Field(default=None, description="Field-level context")


class Page(BaseModel, Generic[T]):
    """A page of results."""

    items: list[T]
    total: int
    page: int
    limit: int

    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.limit))


class Message(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: str
    model_available: bool
    model_version: str | None = None
    weather_provider: str
    site_resolution_status: str
    notes: list[str] = Field(default_factory=list)
