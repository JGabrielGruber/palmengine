"""
Context engine — stack-based scoped execution context.

Frames may hold metadata and/or a bound ``BaseState`` for cooperation with
behavior trees and patterns. State scopes are coordinated through the bound
``BaseState`` when ``state_scope`` is requested on push/scope.
"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.context.base_state import BaseState
from palm.core.context.state_schema import StateSchema
from palm.core.exceptions import ContextError, StateNotConfiguredError

STATE_FRAME_KEY = "state"
STATE_SCOPE_FRAME_KEY = "_state_scope"


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

    @property
    def current_state_scope(self) -> str | None:
        """Return the active state scope on the bound state, if any."""
        state = self.current_state
        return state.current_scope() if state is not None else None

    @property
    def state_scope_stack(self) -> tuple[str, ...]:
        """Return the bound state's scope stack."""
        state = self.current_state
        return state.scope_stack() if state is not None else ()

    @property
    def state_scope_depth(self) -> int:
        """Return nested state scope depth for the bound state."""
        state = self.current_state
        return state.scope_depth() if state is not None else 0

    @property
    def effective_schema(self) -> StateSchema | None:
        """Return the schema active for the current scope on the bound state."""
        state = self.current_state
        return state.effective_schema() if state is not None else None

    def get(self, key: str, default: Any = None) -> Any:
        return self.current.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.current[key] = value

    def bind_state(self, state: BaseState) -> None:
        """Attach ``state`` to the current context frame."""
        self.current[STATE_FRAME_KEY] = state

    def bind_schema(self, schema: StateSchema | None) -> None:
        """Attach ``schema`` to the state bound to the current frame."""
        state = self._require_current_state()
        state.bind_schema(schema)

    def bind_scope_schema(self, scope_name: str, schema: StateSchema | None) -> None:
        """Attach a per-scope schema on the bound state."""
        self._require_current_state().bind_scope_schema(scope_name, schema)

    def restore_state_context(
        self,
        *,
        scope_stack: list[str] | tuple[str, ...] | None = None,
        scope_schemas: dict[str, StateSchema] | None = None,
        schema: StateSchema | None = None,
    ) -> None:
        """Restore schema and scope metadata on the bound state."""
        state = self._require_current_state()
        if schema is not None:
            state.bind_schema(schema)
        if scope_schemas:
            state.restore_scope_schemas(scope_schemas)
        if scope_stack:
            state.restore_scope_stack(scope_stack)

    def enter_state_scope(self, name: str) -> str:
        """Enter a named scope on the state bound to the current frame.

        Prefer :meth:`~palm.core.context.BaseState.scope` on the bound state
        when driving pattern logic directly; this method coordinates the same
        stack for observability via :attr:`current_state_scope`.
        """
        return self._require_current_state().enter_scope(name)

    def exit_state_scope(self) -> str:
        """Exit the innermost scope on the state bound to the current frame."""
        return self._require_current_state().exit_scope()

    @contextmanager
    def state_scope(self, name: str) -> Generator[BaseState, None, None]:
        """Context manager that enters a state scope and yields the bound state."""
        state = self._require_current_state()
        with state.scope(name):
            yield state

    def push(
        self,
        name: str,
        *,
        state: BaseState | None = None,
        state_scope: bool = False,
        **data: Any,
    ) -> dict[str, Any]:
        """Push a new frame, optionally binding execution state."""
        frame = self._make_frame(name, **data)
        if state is not None:
            frame[STATE_FRAME_KEY] = state
        if state_scope:
            target = frame.get(STATE_FRAME_KEY)
            if not isinstance(target, BaseState):
                target = self.current_state
            if not isinstance(target, BaseState):
                raise StateNotConfiguredError(
                    "Cannot push state scope without a bound BaseState",
                )
            target.enter_scope(name)
            frame[STATE_SCOPE_FRAME_KEY] = True
            if STATE_FRAME_KEY not in frame:
                frame[STATE_FRAME_KEY] = target
        self._stack.append(frame)
        return frame

    def pop(self) -> dict[str, Any]:
        if len(self._stack) <= 1:
            raise ContextError("Cannot pop the root context frame")
        frame = self._stack.pop()
        if frame.get(STATE_SCOPE_FRAME_KEY):
            state = self.current_state
            if state is not None:
                state.exit_scope()
        return frame

    @contextmanager
    def scope(
        self,
        name: str,
        *,
        state: BaseState | None = None,
        state_scope: bool = False,
        **data: Any,
    ) -> Generator[dict[str, Any], None, None]:
        frame = self.push(name, state=state, state_scope=state_scope, **data)
        try:
            yield frame
        finally:
            self.pop()

    def frames(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(dict(frame) for frame in self._stack)

    def _make_frame(self, name: str, **data: Any) -> dict[str, Any]:
        return {self._ROOT_KEY: name, **data}

    def _require_current_state(self) -> BaseState:
        state = self.current_state
        if state is None:
            raise StateNotConfiguredError("Context frame has no bound BaseState")
        return state

    def _do_initialize(self, **options: Any) -> None:
        seed = options.get("initial")
        state = options.get("state")
        schema = options.get("schema")
        if isinstance(seed, dict):
            frame = self._make_frame("root", **seed)
        else:
            frame = self._make_frame("root")
        if isinstance(state, BaseState):
            frame[STATE_FRAME_KEY] = state
            if schema is not None:
                state.bind_schema(schema)
        self._stack = [frame]

    def _do_shutdown(self) -> None:
        self._stack = [self._make_frame("root")]