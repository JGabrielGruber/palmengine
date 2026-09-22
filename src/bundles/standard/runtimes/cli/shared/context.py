"""
CLI session context — ApplicationHost-backed commands and queries.

0.58.17: :attr:`bound_surface` is the session-owned surface context truth.
``active_system_session_id`` / assist / instance slots remain transport mirrors
until SI-001 rename (0.58.19). Product door is ``host.session`` only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.adapters import read_model_to_summary
from palm.common.exceptions import InstanceNotFoundError
from palm.common.managers import InstanceManager, InstanceSummary
from palm.core.orchestration import Job
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.definitions.resource import ResourceDefinition
from palm.instances import ProcessInstance, StateSnapshot
from bundles.standard.runtimes.cli.shared.instances import resolve_instance_id as _resolve_instance_id
from palm.services.execution.flows import ReplSession

if TYPE_CHECKING:
    from bundles.standard.app.host.application_host import ApplicationHost
    from bundles.standard.app.kernel import PalmKernel
    from palm.services.session import BoundSurface


@dataclass
class CliContext:
    """
    Shared state for one-shot commands and the REPL.

    All CLI operations route through :class:`~palm.app.host.ApplicationHost`
    for CQRS command dispatch, query serving, and coordinated recovery.
    """

    host: ApplicationHost
    console: Any
    active_instance_id: str | None = None
    active_assist_session_id: str | None = None
    active_assist_scenario_id: str | None = None
    # System session plane bind (0.58.3) — mirror of bound_surface.session_id.
    active_system_session_id: str | None = None
    # Session-owned surface context (0.58.17) — product truth for the walk.
    bound_surface: BoundSurface | None = None
    output_format: str = "table"
    _instance_to_job: dict[str, str] = field(default_factory=dict)
    _repl_session: ReplSession | None = field(default=None, repr=False)

    @property
    def app(self) -> PalmKernel:
        """Infrastructure layer — definitions, storage, runtime registry."""
        return self.host.app

    @property
    def settings(self) -> PalmSettings:
        return self.app.settings

    @property
    def instance_manager(self) -> InstanceManager:
        return self.app.instance_manager

    @property
    def repl(self) -> ReplSession:
        """Stateful REPL handle — tracks the active instance across commands."""
        if self._repl_session is None:
            self._repl_session = ReplSession(self.host.execution.flows)
        return self._repl_session

    def is_runtime_started(self) -> bool:
        return self.host.is_started and bool(self.host.running_runtimes())

    def running_runtime_names(self) -> list[str]:
        return self.host.running_runtimes()

    def set_active(self, instance_id: str, job_id: str) -> None:
        self.clear_active_assist()
        self.active_instance_id = instance_id
        self._instance_to_job[instance_id] = job_id
        self.instance_manager.mark_active(instance_id)
        self.repl.activate(instance_id)
        # Job-path activation still needs a system outside subject (bind law).
        self.bind_system_session(surface="cli")

    def bind_system_session(
        self,
        session_id: str | None = None,
        *,
        create: bool = True,
        surface: str = "cli",
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Bind (or create) a **system** session via product SessionService (0.58.17).

        Installs :attr:`bound_surface` as truth. Mirrors
        :attr:`active_system_session_id` for legacy CLI slots (SI-006 residual).
        Does **not** treat product assist ``session_id`` as the system subject.
        """
        sid = (
            session_id
            or (self.bound_surface.session_id if self.bound_surface else None)
            or self.active_system_session_id
            or ""
        ).strip() or None
        meta = dict(metadata or {})
        svc = getattr(self.host, "session", None)
        if svc is not None and hasattr(svc, "bind_surface"):
            iid = self.active_instance_id
            bound = svc.bind_surface(
                sid,
                create=create,
                metadata=meta or None,
                surface=surface,
                origin="cli",
                instance_id=iid,
                resolve_instance=iid is None,
            )
            self.bound_surface = bound
            self.active_system_session_id = str(bound.session_id)
            return bound
        # Host door fallback (bind_session prefers SessionService when wired)
        bind = self.host.bind_session(
            sid,
            create=create,
            metadata=meta or None,
            surface=surface,
        )
        self.active_system_session_id = str(bind.session_id)
        if svc is not None and hasattr(svc, "surface_from_bind"):
            self.bound_surface = svc.surface_from_bind(bind)
        return bind

    def set_active_assist(self, view: dict[str, Any]) -> None:
        """Track the active assist handle from an assistant envelope.

        Product assist still may use instance-shaped ``session_id`` (SI-001).
        System bind updates :attr:`bound_surface` (0.58.17).
        """
        # Bind law first: outside subject before product assist tracking.
        # 0.58.9: view.session_id is system subject when sess-shaped.
        system_from_view = view.get("session_id")
        if system_from_view and not str(system_from_view).startswith("sess-"):
            system_from_view = None
        self.bind_system_session(
            str(system_from_view) if system_from_view else None,
            surface="cli",
            metadata={"via": "assist"},
        )

        # Product continue handle (SI-001 internal) — instance_id preferred.
        session_id = view.get("instance_id") or view.get("session_id")
        if not session_id:
            return
        if str(session_id).startswith("sess-"):
            # System id only — no product instance yet; leave assist handle unset.
            return
        session_id = str(session_id)
        self.active_assist_session_id = session_id
        scenario_id = view.get("scenario_id")
        self.active_assist_scenario_id = str(scenario_id) if scenario_id else None
        refs = view.get("refs") if isinstance(view.get("refs"), dict) else {}
        job_id = refs.get("job_id")
        # Prefer explicit instance_id when product starts telling the truth (SI-001).
        instance_id = view.get("instance_id") or refs.get("instance_id") or session_id
        instance_id = str(instance_id)
        self.active_instance_id = instance_id
        if self.bound_surface is not None:
            self.bound_surface = self.bound_surface.with_instance(instance_id)
        if job_id:
            self._instance_to_job[instance_id] = str(job_id)
        self.instance_manager.mark_active(instance_id)
        self.repl.activate(instance_id)

    def clear_active_assist(self) -> None:
        self.active_assist_session_id = None
        self.active_assist_scenario_id = None
        # Keep system session across assist clear (walk continues); clear with host stop.

    def list_instance_summaries(self) -> list[InstanceSummary]:
        views = self.host.list_instance_views(include_terminal=True)
        return [read_model_to_summary(view) for view in views]

    def resolve_instance_id(self, ref: str) -> str:
        return _resolve_instance_id(self, ref)

    def get_instance(self, ref: str) -> ProcessInstance:
        instance_id = self.resolve_instance_id(ref)
        return self.instance_manager.get(instance_id)

    def get_instance_status_view(self, ref: str):
        instance_id = self.resolve_instance_id(ref)
        return self.host.get_instance_view(instance_id)

    def list_instance_snapshots(self, instance_id: str) -> list[StateSnapshot]:
        resolved = self.resolve_instance_id(instance_id)
        return self.host.list_instance_snapshots(resolved)

    def resolve_flow(self, ref: str) -> FlowDefinition:
        return self.app.resolve_flow(ref)

    def resolve_process(self, ref: str) -> ProcessDefinition:
        return self.app.resolve_process(ref)

    def resolve_resource(self, ref: str) -> ResourceDefinition:
        return self.app.resolve_resource(ref)

    def submit_flow(
        self,
        ref: FlowDefinition | str,
        *,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        return self.host.submit_flow(ref, job_id=job_id, metadata=metadata)

    def submit_process(
        self,
        ref: ProcessDefinition | str,
        *,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job | list[Job]:
        return self.host.submit_process(ref, job_id=job_id, metadata=metadata)

    def provide_input(self, job_id: str, value: Any) -> str | None:
        return self.host.provide_input(job_id, value)

    def resume_process(self, instance_id: str) -> Job:
        return self.host.resume_process(instance_id)

    def get_job(self, job_id: str) -> Job:
        return self.app.get_job(job_id)

    def resume_job(self, job_id: str) -> None:
        # 0.63.34 — host packaging door, not kernel dig
        self.host.resume_job(job_id)

    def persist_job(self, job: Job) -> None:
        self.app.persist_job(job)

    def resolve_job_id(self, instance_or_job_id: str) -> str:
        if instance_or_job_id in self._instance_to_job:
            return self._instance_to_job[instance_or_job_id]

        try:
            instance_id = self.resolve_instance_id(instance_or_job_id)
        except InstanceNotFoundError:
            return instance_or_job_id

        inst = self.instance_manager.get(instance_id)
        job_id = inst.job_id
        try:
            self.get_job(job_id)
        except JobNotFoundError:
            job = self.host.resume_process(inst.instance_id)
            job_id = job.id
        self.set_active(inst.instance_id, job_id)
        return job_id

    def job_for_instance(self, instance_id: str) -> Job:
        job_id = self.resolve_job_id(instance_id)
        return self.get_job(job_id)
