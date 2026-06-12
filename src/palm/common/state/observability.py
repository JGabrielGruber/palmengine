"""
State observability — emit structured events for scope and value transitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState, StateSchema

if TYPE_CHECKING:
    from palm.core.event import EventEngine

STATE_SCOPE_ENTERED = "palm.state.scope_entered"
STATE_SCOPE_EXITED = "palm.state.scope_exited"
STATE_VALUE_SET = "palm.state.value_set"
STATE_SCHEMA_BOUND = "palm.state.schema_bound"


class EventEngineStateObserver:
    """Forward state transitions to an :class:`~palm.core.event.EventEngine`."""

    def __init__(
        self,
        event_engine: EventEngine,
        *,
        source: str = "state",
        job_id: str | None = None,
        instance_id: str | None = None,
    ) -> None:
        self._event_engine = event_engine
        self._source = source
        self._job_id = job_id
        self._instance_id = instance_id

    def on_scope_enter(self, name: str, *, stack: tuple[str, ...]) -> None:
        self._emit(
            STATE_SCOPE_ENTERED,
            scope=name,
            scope_stack=list(stack),
            scope_depth=len(stack),
        )

    def on_scope_exit(self, name: str, *, stack: tuple[str, ...]) -> None:
        self._emit(
            STATE_SCOPE_EXITED,
            scope=name,
            scope_stack=list(stack),
            scope_depth=len(stack),
        )

    def on_value_set(self, key: str, value: Any, *, scope: str | None) -> None:
        self._emit(
            STATE_VALUE_SET,
            key=key,
            scope=scope,
            has_value=value is not None,
        )

    def on_schema_bound(
        self,
        schema: StateSchema | None,
        *,
        scope: str | None,
    ) -> None:
        payload: dict[str, Any] = {"scope": scope}
        if schema is not None and schema.definition is not None:
            payload["schema"] = dict(schema.definition)
        self._emit(STATE_SCHEMA_BOUND, **payload)

    def _emit(self, event_type: str, **payload: Any) -> None:
        payload.setdefault("source", self._source)
        if self._job_id is not None:
            payload.setdefault("job_id", self._job_id)
        if self._instance_id is not None:
            payload.setdefault("instance_id", self._instance_id)
        self._event_engine.emit(event_type, **payload)


def observe_state(
    state: BaseState,
    event_engine: EventEngine,
    *,
    source: str = "state",
    job_id: str | None = None,
    instance_id: str | None = None,
) -> EventEngineStateObserver:
    """Attach an event-emitting observer to ``state``."""
    observer = EventEngineStateObserver(
        event_engine,
        source=source,
        job_id=job_id,
        instance_id=instance_id,
    )
    state.set_observer(observer)
    return observer