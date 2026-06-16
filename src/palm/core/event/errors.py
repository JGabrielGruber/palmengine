"""
Event dispatch error records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HandlerError:
    """Captured exception from a single handler invocation."""

    event_type: str
    handler: Any
    error: BaseException


@dataclass
class PublishResult:
    """Outcome of a publish cycle."""

    delivered: int = 0
    handler_errors: list[HandlerError] | None = None
    async_scheduled: int = 0

    @property
    def ok(self) -> bool:
        return not self.handler_errors