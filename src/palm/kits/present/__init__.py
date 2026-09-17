"""Present kit — library walk over session + execution (0.69.4).

One object holds one :class:`~palm.services.session.bound_surface.BoundSurface`
and walks existing doors: bind, present, submit, start, attach, focus.

Not a ``PresentService``. Not ``palm.kits.server``. Turn invert: this kit
walks; the pattern fills ``JobInspectable`` / ``InputCapable``. Handle class
name stays unnamed (VISION-NAVIGATOR §5).
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from palm.common.job_inspection import JobContext, inspect_job
from palm.kits.registry import register_kit
from palm.system.subsystems.planes.wait.present import waiting_on_from_job

if TYPE_CHECKING:
    from palm.core.orchestration import Job
    from palm.services.execution.flows.service import FlowExecutionService
    from palm.services.session.bound_surface import BoundSurface
    from palm.services.session.service import SessionService
    from palm.system.runtime.base import BaseRuntime

register_kit(
    "present",
    description="Embedded library walk: bind, present, submit, start, attach, focus",
    module="palm.kits.present",
)


class _Present:
    """Holds one BoundSurface and walks session + execution doors."""

    def __init__(
        self,
        *,
        session: SessionService,
        flows: FlowExecutionService,
        runtime: BaseRuntime,
    ) -> None:
        self._session = session
        self._flows = flows
        self._runtime = runtime
        self._bound: BoundSurface | None = None

    @property
    def bound(self) -> BoundSurface:
        if self._bound is None:
            raise RuntimeError("present kit has no BoundSurface; call bind first")
        return self._bound

    def bind(
        self,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> BoundSurface:
        self._bound = self._session.bind_surface(session_id, **kwargs)
        return self._bound

    def present(self) -> JobContext:
        job = self._focused_job()
        ctx = inspect_job(job)
        waits = tuple(waiting_on_from_job(job))
        if waits and not ctx.waiting_on:
            ctx = replace(ctx, waiting_on=waits)
        return ctx

    def submit(self, value: Any) -> None:
        job = self._focused_job()
        self._runtime.provide_input(job.id, value)
        self._bound = self._session.surface_from_session(self.bound.session_id)

    def start(
        self,
        flow: Any,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: Any = None,
    ) -> BoundSurface:
        self._bound = self._flows.spawn_sibling(
            self.bound.session_id,
            flow,
            by_id=by_id,
            job_id=job_id,
            state=state,
        )
        return self._bound

    def attach(self, instance_id: str) -> BoundSurface:
        self._bound = self._session.attach_after_start(
            self.bound.session_id,
            instance_id,
        )
        return self._bound

    def focus(self, instance_id: str) -> BoundSurface:
        self._bound = self._session.focus(self.bound.session_id, instance_id)
        return self._bound

    def _focused_job(self) -> Job:
        iid = self.bound.instance_id
        if not iid:
            raise RuntimeError("present kit has no continue focus")
        instance = self._runtime.get_instance(iid)
        return self._runtime.get_job(instance.job_id)


def bind(host: Any, session_id: str | None = None, **kwargs: Any) -> _Present:
    """Open a present walk on ``host`` seats and bind an outside session."""
    kit = _Present(
        session=host.session,
        flows=host.execution.flows,
        runtime=host.runtime(),
    )
    kit.bind(session_id, **kwargs)
    return kit


__all__ = ["bind"]
