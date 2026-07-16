"""
Projection framework — event-driven read model maintenance.

To add a projection:

1. Subclass :class:`Projection` in ``palm/common/cqrs/projections/``.
2. Register it on the host :class:`~palm.common.cqrs.projection.ProjectionManager`.
3. Expose read methods through a query handler in :mod:`palm.app.host.wiring.cqrs`.
4. Subscribe to domain events via :meth:`ProjectionManager.attach` (done for each
   runtime and the host bus during :meth:`~palm.app.host.ApplicationHost.start`).
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from palm.common.cqrs.rebuild import ProjectionRebuildPolicy, ProjectionRebuildReport
from palm.core.event import Subscription

if TYPE_CHECKING:
    from palm.core.event import Event, EventEngine


class Projection(ABC):
    """Maintains a read model by reacting to domain events."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable projection identifier."""

    @abstractmethod
    def handles(self, event_type: str) -> bool:
        """Return whether this projection consumes ``event_type``."""

    @abstractmethod
    def apply(self, event: Event) -> None:
        """Update the read model from ``event``."""

    @abstractmethod
    def rebuild(self, *, policy: ProjectionRebuildPolicy | None = None) -> int:
        """Rebuild the read model from authoritative storage. Returns item count."""

    @abstractmethod
    def clear(self) -> None:
        """Remove the projection read model."""


class ProjectionManager:
    """Attach projections to event engines and coordinate rebuild."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._projections: dict[str, Projection] = {}
        self._subscriptions: list[tuple[EventEngine, Subscription]] = []

    def register(self, projection: Projection) -> None:
        with self._lock:
            self._projections[projection.name] = projection

    def get(self, name: str) -> Projection | None:
        with self._lock:
            return self._projections.get(name)

    @property
    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._projections)

    @property
    def projections(self) -> tuple[Projection, ...]:
        with self._lock:
            return tuple(self._projections[name] for name in sorted(self._projections))

    def attach(self, event_engine: EventEngine) -> None:
        """Subscribe all projections to ``event_engine``."""
        if not event_engine.is_initialized:
            event_engine.initialize()

        def fan_out(event: Event) -> None:
            for projection in self.projections:
                if projection.handles(event.type):
                    try:
                        projection.apply(event)
                    except Exception:
                        continue

        subscription = event_engine.subscribe("*", fan_out)
        with self._lock:
            self._subscriptions.append((event_engine, subscription))

    def attach_runtimes(self, app: object) -> None:
        """Attach to every started runtime event bus on a PalmKernel."""
        runtimes = getattr(app, "_runtimes", None)
        if runtimes is None:
            return
        for handle in runtimes.items():
            if handle.is_started:
                self.attach(handle.runtime.event)

    def rebuild_all(
        self,
        *,
        policy: ProjectionRebuildPolicy | None = None,
    ) -> ProjectionRebuildReport:
        """Rebuild every registered projection with optional safeguards."""
        resolved = policy or ProjectionRebuildPolicy()
        report = ProjectionRebuildReport()
        for projection in self.projections:
            count = projection.rebuild(policy=resolved)
            report.counts[projection.name] = count
            if hasattr(projection, "was_rebuild_skipped") and projection.was_rebuild_skipped():
                report.skipped.append(projection.name)
            if getattr(projection, "used_batched_rebuild", False):
                report.batched.append(projection.name)
            warnings = getattr(projection, "rebuild_warnings", None)
            if warnings:
                report.warnings.extend(warnings)
        return report

    def shutdown(self) -> None:
        with self._lock:
            for _, subscription in self._subscriptions:
                subscription.unsubscribe()
            self._subscriptions.clear()
