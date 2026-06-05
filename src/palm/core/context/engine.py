"""
Context engine — stack-based scoped execution context.

Frames may hold metadata and/or a bound ``BaseState`` for cooperation with
behavior trees and patterns.
"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.context.base_state import BaseState
from palm.core.exceptions import ContextError

STATE_FRAME_KEY = "state"


class ContextEngine(BasePalmEngine):
    """Maintains a stack of named execution contexts with push/pop semantics."""

    _ROOT_KEY = "_name"

    def __init__(self) -> None:
        super().__init__(name="context")
        self._stack: list[dict[str, Any]] = [self._make_frame("root")]

    @property
    def current(self) -> dict[str, Any]:
        """The active context frame (mutable metadata dict)."""
        return self._stack[-1]

    @property
    def depth(self) -> int:
        return len(self._stack)

    @property
    def current_name(self) -> str:
        return str(self.current.get(self._ROOT_KEY, "root"))

    @property
    def current_state(self) -> BaseState | None:
        """Return the ``BaseState`` bound to the current frame, if any."""
        value = self.current.get(STATE_FRAME_KEY)
        return value if isinstance(value, BaseState) else None

    def get(self, key: str, default: Any = None) -> Any:
        return self.current.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.current[key] = value

    def bind_state(self, state: BaseState) -> None:
        """Attach ``state`` to the current context frame."""
        self.current[STATE_FRAME_KEY] = state

    def push(
        self,
        name: str,
        *,
        state: BaseState | None = None,
        **data: Any,
    ) -> dict[str, Any]:
        """Push a new frame, optionally binding execution state."""
        frame = self._make_frame(name, **data)
        if state is not None:
            frame[STATE_FRAME_KEY] = state
        self._stack.append(frame)
        return frame

    def pop(self) -> dict[str, Any]:
        if len(self._stack) <= 1:
            raise ContextError("Cannot pop the root context frame")
        return self._stack.pop()

    @contextmanager
    def scope(
        self,
        name: str,
        *,
        state: BaseState | None = None,
        **data: Any,
    ) -> Generator[dict[str, Any], None, None]:
        frame = self.push(name, state=state, **data)
        try:
            yield frame
        finally:
            self.pop()

    def frames(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(dict(frame) for frame in self._stack)

    def _make_frame(self, name: str, **data: Any) -> dict[str, Any]:
        return {self._ROOT_KEY: name, **data}

    def _do_initialize(self, **options: Any) -> None:
        seed = options.get("initial")
        state = options.get("state")
        if isinstance(seed, dict):
            frame = self._make_frame("root", **seed)
        else:
            frame = self._make_frame("root")
        if isinstance(state, BaseState):
            frame[STATE_FRAME_KEY] = state
        self._stack = [frame]

    def _do_shutdown(self) -> None:
        self._stack = [self._make_frame("root")]