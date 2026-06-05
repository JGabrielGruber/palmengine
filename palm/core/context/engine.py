"""
Context engine — scoped execution context and metadata.

Provides a stack of named contexts for runtimes and patterns to attach
session-local data without coupling to CLI or persistence.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from palm.core.base import BasePalmEngine


class ContextEngine(BasePalmEngine):
    """Maintains a stack of named execution contexts."""

    def __init__(self) -> None:
        super().__init__(name="context")
        self._stack: list[dict[str, Any]] = [{}]

    @property
    def current(self) -> dict[str, Any]:
        return self._stack[-1]

    @contextmanager
    def push(self, name: str, **data: Any) -> Generator[dict[str, Any], None, None]:
        ctx = {"_name": name, **data}
        self._stack.append(ctx)
        try:
            yield ctx
        finally:
            self._stack.pop()

    def _do_initialize(self, **options: Any) -> None:
        seed = options.get("initial")
        if isinstance(seed, dict):
            self._stack = [dict(seed)]

    def _do_shutdown(self) -> None:
        self._stack = [{}]
