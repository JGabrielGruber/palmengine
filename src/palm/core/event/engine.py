"""
Event engine — publish/subscribe observability bus.

Supports synchronous in-process dispatch (default), optional async handlers,
context propagation, subscription management, and publish interceptors for
reliable delivery extensions in outer layers.
"""

from __future__ import annotations

import asyncio
import contextvars
import inspect
import threading
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.event.context import EventContext
from palm.core.event.errors import HandlerError, PublishResult
from palm.core.event.subscription import Subscription

EventHandler = Callable[["Event"], Any]
PublishInterceptor = Callable[["Event"], None]

_current_context: contextvars.ContextVar[EventContext | None] = contextvars.ContextVar(
    "palm_event_context",
    default=None,
)


@dataclass(frozen=True)
class Event:
    """Immutable domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    context: EventContext | None = None

    def enriched_payload(self) -> dict[str, Any]:
        """Return payload merged with correlation context for subscribers."""
        merged = dict(self.payload)
        if self.context is not None:
            for key, value in self.context.to_dict().items():
                merged.setdefault(key, value)
        return merged


@dataclass
class _HandlerEntry:
    subscription_id: int
    handler: EventHandler
    priority: int


class EventEngine(BasePalmEngine):
    """
    Production-grade synchronous event bus with optional async handlers.

    Handlers run inline during ``publish`` unless they are coroutine functions,
    in which case they are scheduled on the running event loop or queued for
    :meth:`drain_async_handlers`.
    """

    def __init__(self) -> None:
        super().__init__(name="event")
        self._lock = threading.RLock()
        self._handlers: dict[str, list[_HandlerEntry]] = {}
        self._interceptors: list[tuple[int, PublishInterceptor]] = []
        self._next_subscription_id = 1
        self._pending_async: list[tuple[EventHandler, Event]] = []
        self._drain_tasks: list[asyncio.Task[int]] = []
        self._isolate_handler_errors = True
        self._last_handler_errors: list[HandlerError] = []

    @property
    def last_handler_errors(self) -> list[HandlerError]:
        """Errors captured during the most recent publish cycle."""
        return list(self._last_handler_errors)

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        *,
        priority: int = 0,
    ) -> Subscription:
        """Register ``handler`` for ``event_type`` (or ``*`` for all events)."""
        with self._lock:
            sub_id = self._next_subscription_id
            self._next_subscription_id += 1
            entry = _HandlerEntry(subscription_id=sub_id, handler=handler, priority=priority)
            bucket = self._handlers.setdefault(event_type, [])
            bucket.append(entry)
            bucket.sort(key=lambda item: item.priority, reverse=True)
            return Subscription(event_type=event_type, subscription_id=sub_id, engine=self)

    def unsubscribe(self, subscription: Subscription) -> None:
        """Remove a subscription created via :meth:`subscribe` or :meth:`add_interceptor`."""
        with self._lock:
            if subscription.event_type == "__interceptor__":
                self._interceptors = [
                    item for item in self._interceptors if item[0] != subscription.subscription_id
                ]
                return
            bucket = self._handlers.get(subscription.event_type, [])
            self._handlers[subscription.event_type] = [
                entry for entry in bucket if entry.subscription_id != subscription.subscription_id
            ]

    def add_interceptor(self, interceptor: PublishInterceptor) -> Subscription:
        """
        Register a publish interceptor (e.g. outbox writer in outer layers).

        Interceptors run before handlers unless ``source`` is ``outbox``.
        """
        with self._lock:
            sub_id = self._next_subscription_id
            self._next_subscription_id += 1
            self._interceptors.append((sub_id, interceptor))
            return Subscription(
                event_type="__interceptor__",
                subscription_id=sub_id,
                engine=self,
            )

    def bind_context(self, context: EventContext | None) -> Iterator[None]:
        """Context manager that sets implicit correlation for nested publishes."""
        return self._context_scope(context)

    @contextmanager
    def _context_scope(self, context: EventContext | None) -> Iterator[None]:
        token = _current_context.set(context)
        try:
            yield
        finally:
            _current_context.reset(token)

    def current_context(self) -> EventContext | None:
        """Return the active implicit event context, if any."""
        return _current_context.get()

    def publish(self, event: Event, *, source: str = "live") -> PublishResult:
        """
        Dispatch ``event`` to subscribers.

        ``source`` is ``live`` for normal publishes and ``outbox`` when replaying
        stored events so interceptors can avoid duplicate persistence.
        """
        resolved = self._resolve_context(event)
        if source != "outbox":
            self._run_interceptors(resolved)

        result = PublishResult()
        errors: list[HandlerError] = []

        with self._lock:
            handlers = list(self._handlers.get(resolved.type, []))
            handlers.extend(self._handlers.get("*", []))

        for entry in handlers:
            try:
                outcome = self._invoke_handler(entry.handler, resolved)
                if inspect.isawaitable(outcome):
                    result.async_scheduled += 1
                else:
                    result.delivered += 1
            except Exception as exc:
                if not self._isolate_handler_errors:
                    raise
                errors.append(
                    HandlerError(
                        event_type=resolved.type,
                        handler=entry.handler,
                        error=exc,
                    )
                )

        self._last_handler_errors = errors
        result.handler_errors = errors or None
        return result

    def emit(
        self,
        event_type: str,
        *,
        context: EventContext | None = None,
        event_id: str | None = None,
        **payload: Any,
    ) -> PublishResult:
        """Construct and publish an event."""
        event = Event(
            type=event_type,
            payload=dict(payload),
            context=context,
            id=event_id or uuid.uuid4().hex,
        )
        return self.publish(event)

    async def drain_async_handlers(self) -> int:
        """
        Await queued async handlers and return how many were processed.

        No-op when there is nothing pending.
        """
        pending = self._collect_pending_async()
        if not pending:
            return 0

        processed = 0
        for handler, event in pending:
            await self._await_handler(handler, event)
            processed += 1
        return processed

    def _collect_pending_async(self) -> list[tuple[EventHandler, Event]]:
        with self._lock:
            pending = list(self._pending_async)
            self._pending_async.clear()
        return pending

    def _resolve_context(self, event: Event) -> Event:
        implicit = _current_context.get()
        if event.context is not None and implicit is not None:
            merged = implicit.merged(event.context)
            return Event(
                type=event.type,
                payload=event.payload,
                timestamp=event.timestamp,
                id=event.id,
                context=merged,
            )
        if event.context is not None:
            return event
        if implicit is not None:
            return Event(
                type=event.type,
                payload=event.payload,
                timestamp=event.timestamp,
                id=event.id,
                context=implicit,
            )
        return event

    def _run_interceptors(self, event: Event) -> None:
        with self._lock:
            interceptors = [fn for _, fn in self._interceptors]
        for interceptor in interceptors:
            interceptor(event)

    def _invoke_handler(self, handler: EventHandler, event: Event) -> Any:
        if inspect.iscoroutinefunction(handler):
            with self._lock:
                self._pending_async.append((handler, event))
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return None
            self._drain_tasks.append(loop.create_task(self.drain_async_handlers()))
            return None
        return handler(event)

    async def _await_handler(self, handler: EventHandler, event: Event) -> None:
        try:
            outcome = handler(event)
            if inspect.isawaitable(outcome):
                await outcome
        except Exception as exc:
            if not self._isolate_handler_errors:
                raise
            self._last_handler_errors.append(
                HandlerError(event_type=event.type, handler=handler, error=exc)
            )

    def _do_initialize(self, **options: Any) -> None:
        isolate = options.get("isolate_handler_errors")
        if isinstance(isolate, bool):
            self._isolate_handler_errors = isolate

    def _do_shutdown(self) -> None:
        with self._lock:
            self._handlers.clear()
            self._interceptors.clear()
            self._pending_async.clear()
        self._last_handler_errors.clear()
