"""
Compensation coordinator — event-driven undo hooks for failed commits and sagas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.compensation.context import CompensationContext, CompensationResult
from palm.common.compensation.events import CompensationEventType, CompensationTrigger
from palm.common.compensation.registry import CompensationRegistry
from palm.core.event import Event, EventEngine, Subscription

if TYPE_CHECKING:
    pass

_TRIGGER_EVENTS = frozenset(
    {
        CompensationTrigger.COMMIT_FAILED,
        CompensationTrigger.BACKTRACK_EXECUTED,
        CompensationTrigger.RESOURCE_FAILED,
    }
)


class CompensationCoordinator:
    """
    Subscribes to domain events and runs optional compensation handlers.

    Commit-failure compensation resolves handlers by ``hook`` payload field.
    Resource failures resolve handlers by ``resource_ref`` or ``compensation_key``.
    Additional handlers may register per event type for saga-style flows.
    """

    def __init__(
        self,
        registry: CompensationRegistry,
        event_engine: EventEngine,
    ) -> None:
        self._registry = registry
        self._event_engine = event_engine
        self._subscription: Subscription | None = None

    @property
    def registry(self) -> CompensationRegistry:
        return self._registry

    def attach(self, event_engine: EventEngine | None = None) -> Subscription:
        """Subscribe to compensation trigger events on ``event_engine``."""
        engine = event_engine or self._event_engine
        if not engine.is_initialized:
            engine.initialize()

        def on_event(event: Event) -> None:
            if event.type not in _TRIGGER_EVENTS:
                return
            self.handle(event)

        self._subscription = engine.subscribe("*", on_event)
        return self._subscription

    def attach_runtimes(self, app: object) -> None:
        """Attach to every started runtime event bus on a PalmKernel."""
        runtimes = getattr(app, "_runtimes", None)
        if runtimes is None:
            return
        for handle in runtimes.items():
            if handle.is_started:
                self.attach(handle.runtime.event)

    def handle(self, event: Event) -> list[CompensationResult]:
        """Run compensation for a single trigger event."""
        context = _context_from_event(event)
        results: list[CompensationResult] = []

        if event.type == CompensationTrigger.COMMIT_FAILED:
            hook = context.hook_name
            if hook and self._registry.has_commit_hook(hook):
                result = self._registry.run_commit_hook(hook, context)
                results.append(result)
                self._emit_outcome(event, hook, result)
            elif hook:
                self._event_engine.emit(
                    CompensationEventType.SKIPPED,
                    trigger=event.type,
                    hook=hook,
                    reason="no_handler",
                )
            for resource_ref in _resource_refs_from_payload(context.payload):
                if not self._registry.has_resource(resource_ref):
                    self._event_engine.emit(
                        CompensationEventType.SKIPPED,
                        trigger=event.type,
                        key=resource_ref,
                        reason="no_handler",
                    )
                    continue
                result = self._registry.run_resource_handler(resource_ref, context)
                results.append(result)
                self._emit_resource_outcome(event, resource_ref, result)
            return results

        if event.type == CompensationTrigger.RESOURCE_FAILED:
            resource_ref = context.resource_ref
            if resource_ref and self._registry.has_resource(resource_ref):
                result = self._registry.run_resource_handler(resource_ref, context)
                results.append(result)
                self._emit_resource_outcome(event, resource_ref, result)
            elif resource_ref:
                self._event_engine.emit(
                    CompensationEventType.SKIPPED,
                    trigger=event.type,
                    key=resource_ref,
                    reason="no_handler",
                )
            return results

        for result in self._registry.run_event_handlers(event.type, context):
            results.append(result)
            self._emit_outcome(event, event.type, result)
        return results

    def shutdown(self) -> None:
        if self._subscription is not None:
            self._subscription.unsubscribe()
            self._subscription = None

    def _emit_outcome(self, trigger: Event, key: str, result: CompensationResult) -> None:
        if result.ok:
            self._event_engine.emit(
                CompensationEventType.EXECUTED,
                trigger=trigger.type,
                key=key,
                data=result.data,
            )
        else:
            self._event_engine.emit(
                CompensationEventType.FAILED,
                trigger=trigger.type,
                key=key,
                error=result.error,
            )

    def _emit_resource_outcome(
        self,
        trigger: Event,
        resource_ref: str,
        result: CompensationResult,
    ) -> None:
        if result.ok:
            self._event_engine.emit(
                CompensationEventType.EXECUTED,
                trigger=trigger.type,
                key=resource_ref,
                resource_ref=resource_ref,
                data=result.data,
            )
            self._event_engine.emit(
                "resource.compensated",
                resource_ref=resource_ref,
                trigger=trigger.type,
                data=result.data,
            )
        else:
            self._event_engine.emit(
                CompensationEventType.FAILED,
                trigger=trigger.type,
                key=resource_ref,
                resource_ref=resource_ref,
                error=result.error,
            )


def _context_from_event(event: Event) -> CompensationContext:
    payload = event.enriched_payload()
    instance_id = payload.get("instance_id")
    job_id = payload.get("job_id")
    if event.context is not None:
        instance_id = instance_id or event.context.instance_id
        job_id = job_id or event.context.job_id
    resource_ref = _str_or_none(
        payload.get("compensation_key") or payload.get("resource_ref"),
    )
    return CompensationContext(
        trigger_event=event.type,
        payload=dict(payload),
        hook_name=_str_or_none(payload.get("hook")),
        resource_ref=resource_ref,
        wizard_name=_str_or_none(payload.get("wizard")),
        error=_str_or_none(payload.get("error")),
        instance_id=_str_or_none(instance_id),
        job_id=_str_or_none(job_id),
    )


def _resource_refs_from_payload(payload: dict[str, Any]) -> list[str]:
    refs = payload.get("resource_refs")
    if isinstance(refs, list):
        return [str(item) for item in refs if item]
    invocations = payload.get("resource_invocations")
    if isinstance(invocations, list):
        keys: list[str] = []
        seen: set[str] = set()
        for entry in invocations:
            if not isinstance(entry, dict):
                continue
            key = entry.get("compensation_key") or entry.get("resource_ref")
            if not key or key in seen:
                continue
            seen.add(str(key))
            keys.append(str(key))
        return keys
    return []


def _str_or_none(value: Any) -> str | None:
    return str(value) if value is not None else None
