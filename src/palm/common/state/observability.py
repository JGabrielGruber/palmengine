"""
State observability — structured events for scope and schema transitions.

Value-change events are opt-in because wizard and behavior-tree ticks can be
chatty. Scope and schema events are enabled by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState, StateSchema
from palm.core.event import EventContext

if TYPE_CHECKING:
    from palm.core.event import EventEngine

STATE_SCOPE_ENTERED = "palm.state.scope_entered"
STATE_SCOPE_EXITED = "palm.state.scope_exited"
STATE_VALUE_SET = "palm.state.value_set"
STATE_SCHEMA_BOUND = "palm.state.schema_bound"

_DEFAULT_IGNORED_PREFIXES = ("__wizard__", "__parallel__", "__branch_state__", "__bt_", "__palm:")


@dataclass(frozen=True)
class StateObserverConfig:
    """Tune which state transitions emit events."""

    emit_scope_events: bool = True
    emit_value_events: bool = False
    emit_schema_events: bool = True
    ignored_key_prefixes: tuple[str, ...] = _DEFAULT_IGNORED_PREFIXES


class EventEngineStateObserver:
    """Forward selected state transitions to an :class:`~palm.core.event.EventEngine`."""

    def __init__(
        self,
        event_engine: EventEngine,
        *,
        config: StateObserverConfig | None = None,
        source: str = "state",
        job_id: str | None = None,
        instance_id: str | None = None,
    ) -> None:
        self._event_engine = event_engine
        self._config = config or StateObserverConfig()
        self._source = source
        self._job_id = job_id
        self._instance_id = instance_id

    def on_scope_enter(self, name: str, *, stack: tuple[str, ...]) -> None:
        if not self._config.emit_scope_events:
            return
        self._emit(
            STATE_SCOPE_ENTERED,
            scope=name,
            scope_stack=list(stack),
            scope_depth=len(stack),
        )

    def on_scope_exit(self, name: str, *, stack: tuple[str, ...]) -> None:
        if not self._config.emit_scope_events:
            return
        self._emit(
            STATE_SCOPE_EXITED,
            scope=name,
            scope_stack=list(stack),
            scope_depth=len(stack),
        )

    def on_value_set(self, key: str, value: Any, *, scope: str | None) -> None:
        if not self._config.emit_value_events:
            return
        if _is_ignored_key(key, self._config.ignored_key_prefixes):
            return
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
        if not self._config.emit_schema_events:
            return
        payload: dict[str, Any] = {"scope": scope}
        if schema is not None and schema.definition is not None:
            payload["schema_type"] = schema.definition.get("type")
            if scope is None:
                payload["schema"] = dict(schema.definition)
        self._emit(STATE_SCHEMA_BOUND, **payload)

    def _emit(self, event_type: str, **payload: Any) -> None:
        payload.setdefault("source", self._source)
        context = EventContext(
            job_id=self._job_id,
            instance_id=self._instance_id,
        )
        self._event_engine.emit(event_type, context=context, **payload)


def observe_state(
    state: BaseState,
    event_engine: EventEngine,
    *,
    config: StateObserverConfig | None = None,
    source: str = "state",
    job_id: str | None = None,
    instance_id: str | None = None,
) -> EventEngineStateObserver:
    """Attach a filtered event-emitting observer to ``state``."""
    observer = EventEngineStateObserver(
        event_engine,
        config=config,
        source=source,
        job_id=job_id,
        instance_id=instance_id,
    )
    state.set_observer(observer)
    return observer


def _is_ignored_key(key: str, prefixes: tuple[str, ...]) -> bool:
    return any(key.startswith(prefix) for prefix in prefixes)
