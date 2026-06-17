"""
Compensation handler registry — optional saga-style undo hooks.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.common.compensation.context import CompensationContext, CompensationResult

CompensationHandler = Callable[["CompensationContext"], "CompensationResult"]


class CompensationRegistry:
    """
    Thread-safe registry of compensation handlers.

    Handlers are keyed by commit hook name and/or trigger event type.
    Register during bootstrap — never from job-drive hot paths.
    """

    def __init__(self) -> None:
        self._by_hook: dict[str, CompensationHandler] = {}
        self._by_resource: dict[str, CompensationHandler] = {}
        self._by_event: dict[str, list[CompensationHandler]] = {}
        self._lock = threading.RLock()

    def register_for_commit_hook(self, hook_name: str, handler: CompensationHandler) -> None:
        """Undo handler for a named wizard commit hook (e.g. on commit failure)."""
        if not hook_name:
            raise ValueError("Commit hook name must be non-empty")
        with self._lock:
            self._by_hook[hook_name] = handler

    def register_for_resource(self, resource_ref: str, handler: CompensationHandler) -> None:
        """Undo handler for a mutating resource invoke (keyed by ``resource_ref`` or compensation key)."""
        if not resource_ref:
            raise ValueError("Resource reference must be non-empty")
        with self._lock:
            self._by_resource[resource_ref] = handler

    def register_for_event(self, event_type: str, handler: CompensationHandler) -> None:
        """Handler invoked for every matching domain event."""
        if not event_type:
            raise ValueError("Event type must be non-empty")
        with self._lock:
            bucket = self._by_event.setdefault(event_type, [])
            if handler not in bucket:
                bucket.append(handler)

    def has_commit_hook(self, hook_name: str) -> bool:
        with self._lock:
            return hook_name in self._by_hook

    def has_resource(self, resource_ref: str) -> bool:
        with self._lock:
            return resource_ref in self._by_resource

    def commit_hook_names(self) -> list[str]:
        with self._lock:
            return sorted(self._by_hook)

    def resource_names(self) -> list[str]:
        with self._lock:
            return sorted(self._by_resource)

    def handlers_for_event(self, event_type: str) -> list[CompensationHandler]:
        with self._lock:
            return list(self._by_event.get(event_type, ()))

    def handler_for_commit_hook(self, hook_name: str) -> CompensationHandler | None:
        with self._lock:
            return self._by_hook.get(hook_name)

    def handler_for_resource(self, resource_ref: str) -> CompensationHandler | None:
        with self._lock:
            return self._by_resource.get(resource_ref)

    def run_commit_hook(self, hook_name: str, context: CompensationContext) -> CompensationResult:
        from palm.common.compensation.context import CompensationResult

        with self._lock:
            handler = self._by_hook.get(hook_name)
        if handler is None:
            return CompensationResult.failure(f"No compensation handler for hook {hook_name!r}")
        try:
            return handler(context)
        except Exception as exc:
            return CompensationResult.failure(str(exc))

    def run_resource_handler(
        self, resource_ref: str, context: CompensationContext
    ) -> CompensationResult:
        from palm.common.compensation.context import CompensationResult

        with self._lock:
            handler = self._by_resource.get(resource_ref)
        if handler is None:
            return CompensationResult.failure(
                f"No compensation handler for resource {resource_ref!r}",
            )
        try:
            return handler(context)
        except Exception as exc:
            return CompensationResult.failure(str(exc))

    def run_event_handlers(
        self, event_type: str, context: CompensationContext
    ) -> list[CompensationResult]:
        from palm.common.compensation.context import CompensationResult

        results: list[CompensationResult] = []
        for handler in self.handlers_for_event(event_type):
            try:
                results.append(handler(context))
            except Exception as exc:
                results.append(CompensationResult.failure(str(exc)))
        return results


_default_registry = CompensationRegistry()


def default_compensation_registry() -> CompensationRegistry:
    return _default_registry