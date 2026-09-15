"""
ApplicationHost — top-level Palm orchestrator with CQRS command/query routing.
"""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Any, Self

from palm.app.bootstrap import (
    composition_profile_from_settings,
    deployment_profile_from_settings,
)
from palm.app.host.boot.host_schedule import build_host_handlers
from palm.app.host.boot.modes import BootMode, resolve_boot_mode
from palm.app.host.composition import CompositionProfile
from palm.app.host.event_recorder import HostEventRecorder, RecordedEvent
from palm.app.host.events import HostEventType
from palm.app.host.lifecycle import RecoveryCoordinator, RuntimeSpawner
from palm.app.host.observability import HostObservability
from palm.app.host.roles import DeploymentProfile
from palm.app.host.router import RuntimeRouter
from palm.app.host.services import HostServiceContext, core_service_registry
from palm.app.host.services.packaging import apply_product_packaging
from palm.app.host.wiring import (
    build_pattern_projections,
    wire_command_bus,
    wire_query_bus,
)
from palm.app.host.workplane import WorkPlaneCoordinator
from palm.app.kernel import PalmKernel
from palm.app.settings import PalmSettings
from palm.common.cqrs.bus import CommandBus, QueryBus
from palm.common.cqrs.command import (
    Command,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitProcessCommand,
)
from palm.common.cqrs.projection import ProjectionManager
from palm.common.cqrs.projections.instance_index import (
    InstanceIndexProjection,
    InstanceReadModel,
)
from palm.common.cqrs.projections.job_status_board import (
    JobStatusBoardProjection,
    JobStatusReadModel,
)
from palm.common.cqrs.projections.resource_invocation import (
    ResourceInvocationProjection,
)
from palm.common.cqrs.query import (
    GetInstanceStatusQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    Query,
)
from palm.common.cqrs.schemas import build_schema_registry
from palm.common.events.external import WebhookDispatcher
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine
from palm.core.structure import CAPABILITY_ANALYTICS, CAPABILITY_PROJECTIONS
from palm.kits.server.cqrs import wire_standalone_query_bus
from palm.patterns.wizard.bindings.cqrs.projection import (
    WizardProgressReadModel,
)
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    ListWizardProgressQuery,
)
from palm.system.boot import HOST_PHASES, BootContext, walk_schedule
from palm.system.log import get_system_log

if TYPE_CHECKING:
    from palm.core.orchestration import Job
    from palm.core.resource import ProviderResult
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition
    from palm.system.runtime.base import BaseRuntime


class ApplicationHost:
    """
    Composition-root shell — roles, CQRS, projections, recovery collaborators.

    **Start law lives in** ``palm.app.host.boot`` (0.59.4+). ``start()`` walks
    ``HOST_PHASES``; do not grow private boot order here — add a host phase
    handler under boot.

    :class:`~palm.app.kernel.PalmKernel` remains the infrastructure layer (shared
    storage, runtime registry). After start, the host owns command dispatch,
    query serving, worker routing, and background services::

        host = ApplicationHost(profile=DeploymentProfile.all_in_one())
        host.start()
        job = host.execute(SubmitFlowCommand(flow="my_flow"))
        rows = host.ask(ListInstancesQuery(include_terminal=False))
        host.shutdown()
    """

    def __init__(
        self,
        settings: PalmSettings | None = None,
        *,
        profile: DeploymentProfile | None = None,
        composition: CompositionProfile | None = None,
        storage: StorageEngine | None = None,
        boot_mode: BootMode | str | None = None,
    ) -> None:
        self.settings = settings or PalmSettings()
        mode = resolve_boot_mode(boot_mode)
        self.boot_mode = mode
        # Mode supplies defaults only when caller omits profile/composition.
        # Resolve deployment first so settings→composition can fold role membership
        # (0.59.5) without a second OR at phase time.
        self.profile = (
            profile
            if profile is not None
            else (
                mode.deployment
                if mode is not None
                else deployment_profile_from_settings(self.settings)
            )
        )
        if composition is not None:
            self.composition = composition
        elif mode is not None:
            self.composition = mode.composition
        else:
            # 0.63.12 — deployment roles seed composition when no BootMode
            # (server/worker/all_in_one roles), else settings-composed all_in_one.
            from palm.app.host.composition import CompositionProfile
            from palm.system.structure.seed import boot_mode_name_for_deployment

            seed_name = boot_mode_name_for_deployment(self.profile)
            if seed_name == "server":
                # Server role — full surfaces + drain membership intent
                self.composition = CompositionProfile.server()
            elif seed_name == "worker":
                self.composition = CompositionProfile.worker()
            elif seed_name == "cli":
                self.composition = CompositionProfile.cli()
            else:
                # all_in_one and unknown: settings-composed (capabilities from flags)
                self.composition = composition_profile_from_settings(
                    self.settings, deployment=self.profile
                )
        self._app = PalmKernel(self.settings, storage=storage)
        self._event = EventEngine()
        self._command_bus = CommandBus()
        self._query_bus = QueryBus()
        self._router = RuntimeRouter(self._app)
        self._projection_manager = ProjectionManager()
        self._instance_projection: InstanceIndexProjection | None = None
        self._pattern_projections: dict[str, Any] = {}
        self._resource_projection: ResourceInvocationProjection | None = None
        self._job_board_projection: JobStatusBoardProjection | None = None
        self._worker_coordinator: Any | None = None
        self._event_recorder = HostEventRecorder()
        self._schema_registry: Any | None = None
        self._inspect: Any | None = None
        self._session: Any | None = None
        self._definitions: Any | None = None
        self._execution: Any | None = None
        self._assist: Any | None = None
        self._design: Any | None = None
        self._analytics: Any | None = None
        self._started = False
        self._signal_stop = threading.Event()
        self._last_boot_walk: list[Any] | None = None
        self._observability = HostObservability(self)
        self._workplane = WorkPlaneCoordinator(self)
        self._spawner = RuntimeSpawner(self)
        self._recovery = RecoveryCoordinator(self)

    @classmethod
    def for_mode(
        cls,
        mode: BootMode | str,
        *,
        settings: PalmSettings | None = None,
        profile: DeploymentProfile | None = None,
        composition: CompositionProfile | None = None,
        storage: StorageEngine | None = None,
        server_port: int | None = None,
    ) -> Self:
        """Build a host pinned to a named boot mode (0.59.6+ dogfood entry).

        Prefer this over hand-assembling profile/composition when you want a
        declared phenotype (``safe`` / ``test`` / ``dev`` / shapes).

        When ``settings`` is omitted and the mode is ``safe`` or ``test``, uses
        :meth:`PalmSettings.for_tests` with ``load_examples=False`` (CI isolation).
        Other modes default to a plain :class:`PalmSettings` — pass
        ``PalmSettings.for_tests(...)`` in CI for full/shape dogfood.

        ``server_port`` (0.59.7): when the mode's deployment has ``server`` and
        ``profile`` is omitted, pin the bind port (use ``0`` for ephemeral CI).
        """
        from dataclasses import replace

        resolved = resolve_boot_mode(mode)
        if resolved is None:
            raise ValueError("for_mode requires a boot mode name or BootMode")
        if settings is None:
            if resolved.name in ("safe", "test"):
                settings = PalmSettings.for_tests(load_examples=False)
            else:
                settings = PalmSettings()
        if profile is None and server_port is not None:
            if not resolved.deployment.server:
                raise ValueError(
                    f"server_port requires a server deployment; "
                    f"mode {resolved.name!r} has server={resolved.deployment.server}"
                )
            profile = replace(resolved.deployment, server_port=server_port)
        return cls(
            settings=settings,
            boot_mode=resolved,
            profile=profile,
            composition=composition,
            storage=storage,
        )

    @property
    def app(self) -> PalmKernel:
        """Infrastructure layer — storage and runtime registry."""
        return self._app

    @property
    def event(self) -> EventEngine:
        """Host-level coordination bus."""
        return self._event

    @property
    def system_log(self):
        """Process system log (ordered boot / system narrative). See docs/SYSTEM-LOG.md."""
        return get_system_log()

    @property
    def commands(self) -> CommandBus:
        return self._command_bus

    @property
    def queries(self) -> QueryBus:
        return self._query_bus

    @property
    def schemas(self):
        """CQRS schema registry for validation and introspection."""
        return self._schema_registry

    @property
    def inspect(self):
        """Product inspect door — doctor / list / cancel / present (0.61.4 / SD-007)."""
        return self._inspect

    @property
    def system(self):
        """Deprecated alias for :attr:`inspect` (SD-007 migration)."""
        return self._inspect

    @property
    def session(self):
        """Product session door (0.58.12) — bind, continue target, journey, watches.

        Surfaces use this instead of reinventing plane access. Plane remains law.
        """
        return self._session

    @property
    def definitions(self):
        """Definition catalog service API."""
        return self._definitions

    @property
    def execution(self):
        """Execution service API (flows, providers, processes, workloads)."""
        return self._execution

    @property
    def assist(self):
        """Assist operator guidance service API."""
        return self._assist

    @property
    def design(self):
        """Design service API — propose/validate/impact/commit revisions."""
        return self._design

    @property
    def analytics(self):
        """Analytics organ — live install read (0.67.17)."""
        try:
            return self.runtime().install.analytics
        except Exception:
            return None

    @property
    def event_journal(self):
        """Append-only event journal (0.38) — offsets + redrive."""
        return self._workplane.event_journal

    @property
    def inbound(self):
        """Inbound resource bindings (0.43) — webhook/stream → WorkIntent."""
        return self._workplane.inbound

    @property
    def router(self) -> RuntimeRouter:
        return self._router

    def _runtime_event_engine(self) -> EventEngine:
        """Orchestration bus — ``job.completed`` and peers emit here, not on host coordination bus."""
        try:
            runtime = self._app.runtime()
            engine = runtime.event
            if engine.is_initialized:
                return engine
        except Exception:
            pass
        if not self._event.is_initialized:
            self._event.initialize()
        return self._event

    def pattern_projection(self, name: str) -> Any | None:
        return self._pattern_projections.get(name)

    @property
    def webhook_dispatcher(self) -> WebhookDispatcher | None:
        # 0.67.14: live install read so mount/omit/health see the same object.
        try:
            return self.runtime().install.webhook
        except Exception:
            return None

    @property
    def last_recovery(self) -> dict[str, Any] | None:
        return self._recovery.last_recovery

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def storage(self) -> StorageEngine:
        return self._app.storage

    @property
    def instance_manager(self):
        return self._app.instance_manager

    def runtime(self, name: str | None = None) -> BaseRuntime:
        return self._app.runtime(name)

    @property
    def session_plane(self) -> Any | None:
        """System session plane on the primary runtime (0.58), if started."""
        try:
            runtime = self._app.runtime()
        except Exception:
            return None
        return getattr(runtime, "session_plane", None)

    def bind_session(
        self,
        session_id: str | None = None,
        *,
        create: bool = True,
        metadata: dict[str, Any] | None = None,
        surface: str | None = None,
    ) -> Any:
        """Bind law entry for host surfaces (0.58.3 / 0.58.12 via SessionService).

        Resolves or creates a **system** session. Prefer product
        :attr:`session` for new surface code.
        """
        self._require_started()
        if self._session is not None:
            return self._session.bind(
                session_id,
                create=create,
                metadata=metadata,
                surface=surface,
            )
        plane = self.session_plane
        if plane is None:
            raise RuntimeError("ApplicationHost has no session plane; primary runtime not ready")
        return plane.bind(
            session_id,
            create=create,
            metadata=metadata,
            surface=surface,
        )

    def inspect_session(self, session_id: str) -> dict[str, Any]:
        """Session journey view (instances + open waits). Inspect only (0.58.5)."""
        self._require_started()
        if self._session is not None:
            return self._session.inspect(session_id)
        plane = self.session_plane
        if plane is None:
            raise RuntimeError("ApplicationHost has no session plane; primary runtime not ready")
        return plane.inspect(session_id)

    def resolve_session_continue(self, session_id: str) -> str | None:
        """Instance id under system session for continue (0.58.8). Not resume."""
        self._require_started()
        if self._session is not None:
            return self._session.resolve_continue_instance(session_id)
        plane = self.session_plane
        if plane is None:
            raise RuntimeError("ApplicationHost has no session plane; primary runtime not ready")
        return plane.resolve_continue_instance(session_id)

    def require_session_owns_instance(self, session_id: str, instance_id: str) -> Any:
        """SI-015 owner gate (0.58.11): bound session must own instance."""
        self._require_started()
        if self._session is not None:
            return self._session.require_owned_instance(session_id, instance_id)
        plane = self.session_plane
        if plane is None:
            raise RuntimeError("ApplicationHost has no session plane; primary runtime not ready")
        return plane.require_owned_instance(session_id, instance_id)

    def session_event_matches(self, session_id: str, event: Any) -> bool:
        """Whether an event belongs to the system session (watch filter)."""
        self._require_started()
        if self._session is not None:
            return self._session.event_matches(session_id, event=event)
        plane = self.session_plane
        if plane is None:
            raise RuntimeError("ApplicationHost has no session plane; primary runtime not ready")
        return bool(plane.event_matches(session_id, event=event))

    def start(self, **options: Any) -> Self:
        """Hand control to the host boot schedule (``HOST_PHASES``).

        0.59.4 — no private soup here. Rules live in
        ``palm.app.host.boot.host_schedule``. Observation via SystemLog.
        """
        if self._started:
            return self

        slog = get_system_log()
        roles = sorted(self.profile.roles)
        mode_name = self.boot_mode.name if self.boot_mode is not None else None
        ctx = BootContext(schedule="host", mode=mode_name)
        membership = self.membership_snapshot()
        services_s = ",".join(membership["services"]) or "(none)"
        surfaces_s = ",".join(membership["surfaces"]) or "(none)"
        capabilities_s = ",".join(membership["capabilities"]) or "(none)"
        # Lifecycle: phenotype always on boot.start (pain-point visibility).
        # System level: dedicated membership event when log ≥ system.
        slog.info(
            "boot.start",
            "host boot start",
            schedule="host",
            mode=mode_name,
            roles=",".join(roles) or "(none)",
            services=services_s,
            surfaces=surfaces_s,
            capabilities=capabilities_s,
            composition_services=len(self.composition.services),
            composition_surfaces=len(self.composition.surfaces),
            composition_capabilities=len(self.composition.capabilities),
            primary=self._app.primary_name,
        )
        slog.system(
            "membership",
            "composition membership",
            schedule="host",
            mode=mode_name,
            services=services_s,
            surfaces=surfaces_s,
            capabilities=capabilities_s,
        )
        try:
            # Boot owns order + handlers; this shell is the structure target.
            self._last_boot_walk = walk_schedule(
                HOST_PHASES,
                build_host_handlers(self, options),
                ctx=ctx,
                log=slog,
                require_handlers=True,
            )
        except Exception as exc:
            slog.emit(
                1,
                "boot.fail",
                f"host boot fail: {type(exc).__name__}: {exc}",
                schedule="host",
                mode=mode_name,
                reason=f"{type(exc).__name__}: {exc}",
            )
            raise
        return self

    def membership_snapshot(self) -> dict[str, list[str]]:
        """Declared composition membership (services / surfaces / capabilities).

        0.59.5 — doctor and system log use this as the single membership report.
        """
        return {
            "services": list(self.composition.services),
            "surfaces": list(self.composition.surfaces),
            "capabilities": sorted(self.composition.capabilities),
        }

    @property
    def boot_walk(self) -> list[dict[str, Any]] | None:
        """Last host schedule walk as plain dicts (after ``start``), or None.

        0.59.6 — public dogfood surface so tests and doctor need not touch
        ``_last_boot_walk``. Each row matches :meth:`WalkedPhase.to_dict`.
        """
        if self._last_boot_walk is None:
            return None
        return [w.to_dict() for w in self._last_boot_walk]

    def shutdown(self) -> None:
        """Stop services, projections, and all runtimes."""
        if not self._started:
            return

        slog = get_system_log()
        slog.info("shutdown.start", "host shutdown start", schedule="host")
        # Freeze supervised loops before packaging teardown. Start is
        # system.background.start; runtime.stop stops the supervisor again.
        try:
            supervisor = self.runtime().supervisor
        except Exception:
            supervisor = None
        if supervisor is not None:
            try:
                supervisor.stop()
            except Exception:
                pass
        self._workplane.stop_inbound()

        try:
            from palm.services.analytics.dashboards import attach_dashboard_store

            attach_dashboard_store(None)
        except Exception:
            pass

        self._recovery.stop()
        self._event_recorder.shutdown()
        self._projection_manager.shutdown()
        self._event.emit(HostEventType.SHUTDOWN, primary=self._app.primary_name)
        self._app.shutdown()
        self._event.shutdown()
        self._started = False
        self._signal_stop.set()
        slog.info("shutdown.end", "host shutdown end", schedule="host")

    def execute(self, command: Command) -> Any:
        """Dispatch a write-side command through the host command bus."""
        self._require_started()
        result = self._command_bus.dispatch(command)
        self._event.emit(
            HostEventType.COMMAND_DISPATCHED,
            command=type(command).__name__,
            runtime=self._router.route_job_runtime(getattr(command, "runtime_name", None)),
        )
        return result

    def ask(self, query: Query) -> Any:
        """Execute a read-side query through the host query bus."""
        self._require_started()
        return self._query_bus.ask(query)

    def run_until_signal(self) -> None:
        """Block until SIGINT or SIGTERM."""
        if not self._started:
            raise RuntimeError("ApplicationHost is not started; call start() first")

        self._signal_stop.clear()

        def _handle_signal(*_: object) -> None:
            self._signal_stop.set()

        previous_int = signal.signal(signal.SIGINT, _handle_signal)
        previous_term = signal.signal(signal.SIGTERM, _handle_signal)
        try:
            self._signal_stop.wait()
        finally:
            signal.signal(signal.SIGINT, previous_int)
            signal.signal(signal.SIGTERM, previous_term)

    def list_instance_views(
        self,
        *,
        status: str | None = None,
        flow_name: str | None = None,
        include_terminal: bool = True,
        limit: int | None = None,
    ) -> list[InstanceReadModel]:
        return self.ask(
            ListInstancesQuery(
                status=status,
                flow_name=flow_name,
                include_terminal=include_terminal,
                limit=limit,
            )
        )

    def get_instance_view(self, instance_id: str) -> InstanceReadModel | None:
        return self.ask(GetInstanceStatusQuery(instance_id=instance_id))

    def list_instance_snapshots(self, instance_id: str) -> list:
        return self.ask(ListInstanceSnapshotsQuery(instance_id=instance_id))

    def get_wizard_progress(
        self,
        *,
        instance_id: str | None = None,
        job_id: str | None = None,
    ) -> WizardProgressReadModel | None:
        return self.ask(GetWizardProgressQuery(instance_id=instance_id, job_id=job_id))

    def list_job_views(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[JobStatusReadModel]:
        return self.ask(ListJobStatusQuery(status=status, limit=limit))

    def list_wizard_progress_views(
        self,
        *,
        limit: int | None = 10,
        active_only: bool = False,
    ) -> list[WizardProgressReadModel]:
        return self.ask(ListWizardProgressQuery(limit=limit, active_only=active_only))

    def recent_host_events(self, *, limit: int = 10) -> list[RecordedEvent]:
        return self._event_recorder.recent(limit=limit)

    def invoke_resource(
        self,
        resource_ref: str | None = None,
        *,
        provider: str | None = None,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        state: Any = None,
        resource_id: str | None = None,
        runtime_name: str | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        """Invoke a resource definition or direct provider on the host runtime.

        **0.63.33:** host packaging door for business start — admission fail closed
        (ports remain a second admission check; product façades are preferred
        for surfaces).
        """
        self._require_business_admission()
        return self.app.invoke_resource(
            resource_ref,
            provider=provider,
            action=action,
            params=params,
            state=state,
            resource_id=resource_id,
            runtime_name=runtime_name,
            **kwargs,
        )

    def submit_flow(
        self,
        ref: FlowDefinition | str,
        *,
        runtime_name: str | None = None,
        by_id: bool = False,
        job_id: str | None = None,
        state: Any = None,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> Job:
        """Submit a flow. Optional ``session_id`` is the system session owner (0.58.4).

        Job metadata and edge use one name: ``session_id`` (system subject only).

        **0.63.33:** host packaging door for business start — admission fail closed.
        """
        self._require_business_admission()
        meta = dict(metadata or {})
        sid = session_id or meta.get("session_id") or ""
        sid = str(sid).strip() if sid else ""
        if sid:
            meta["session_id"] = sid
        return self.execute(
            SubmitFlowCommand(
                flow=ref,
                runtime_name=runtime_name,
                by_id=by_id,
                job_id=job_id,
                state=state,
                metadata=meta,
            )
        )

    def submit_process(
        self,
        ref: ProcessDefinition | str,
        *,
        runtime_name: str | None = None,
        by_id: bool = False,
        job_id: str | None = None,
        state: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job | list[Job]:
        """Submit a process.

        **0.63.33:** host packaging door for business start — admission fail closed.
        """
        self._require_business_admission()
        return self.execute(
            SubmitProcessCommand(
                process=ref,
                runtime_name=runtime_name,
                by_id=by_id,
                job_id=job_id,
                state=state,
                metadata=dict(metadata or {}),
            )
        )

    def provide_input(
        self, job_id: str, value: Any, *, runtime_name: str | None = None
    ) -> str | None:
        """Provide interactive input for a waiting job.

        **0.63.33:** host packaging door for business start — admission fail closed.
        """
        self._require_business_admission()
        return self.execute(
            ProvideInputCommand(
                job_id=job_id,
                value=value,
                runtime_name=runtime_name,
            )
        )

    def resume_process(self, instance_id: str, *, runtime_name: str | None = None) -> Job:
        """Resume a process/instance (product continue packaging door).

        **0.63.33:** host packaging door for business continue — admission fail closed.
        """
        self._require_business_admission()
        return self.execute(
            ResumeProcessCommand(
                instance_id=instance_id,
                runtime_name=runtime_name,
            )
        )

    def resume_job(self, job_id: str, *, runtime_name: str | None = None) -> None:
        """Resume orchestration for a job (packaging continue door).

        **0.63.34:** host packaging door for business continue — admission fail
        closed; port remains a second admission check. Surfaces must use this
        instead of the kernel.
        """
        self._require_business_admission()
        self._app.resume_job(job_id, runtime_name=runtime_name)

    def running_runtimes(self) -> list[str]:
        return self._app.running()

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.shutdown()

    def _start_server_surface(self) -> None:
        if not self.profile.server:
            return
        runtime = self._app.runtime("server")
        attach = getattr(runtime, "attach_host", None)
        if callable(attach):
            attach(self)
        start_http = getattr(runtime, "start_http", None)
        if callable(start_http):
            start_http(host=self.profile.server_host, port=self.profile.server_port)

    def _resolve_execution_runtime(self, runtime_name: str | None = None) -> BaseRuntime:
        resolved = self._router.route_job_runtime(runtime_name)
        return self._app.runtime(resolved)

    def _wire_cqrs(self) -> None:
        wire_command_bus(self._command_bus, self._app, self._router)
        # 0.67.10: host slots alias the install organ. Membership is DNA
        # (has_capability). Omit is embedded/worker DNA. Pattern extras stay host.
        if self.admission.has_capability(CAPABILITY_PROJECTIONS):
            # 0.67.10: host slots alias the install organ. Do not rebuild core.
            try:
                bag = self.runtime().install.projections
            except Exception:
                bag = None
            if bag is None:
                wire_standalone_query_bus(self._query_bus, self.runtime())
            else:
                manager = getattr(bag, "manager", None)
                if manager is not None:
                    self._projection_manager = manager
                self._instance_projection = bag.instance
                self._resource_projection = bag.resource
                self._job_board_projection = bag.job_board
                self._pattern_projections = build_pattern_projections(self._app.storage)
                for projection in self._pattern_projections.values():
                    self._projection_manager.register(projection)
                wire_query_bus(
                    self._query_bus,
                    app=self._app,
                    instances=self._instance_projection,
                    pattern_projections=self._pattern_projections,
                    resource_invocations=self._resource_projection,
                    job_board=self._job_board_projection,
                    instance_manager=self._app.instance_manager,
                )
        else:
            # 0.51.6: projection-less (lean) shape — serve reads direct-from-runtime,
            # reusing the standalone read handlers over the host's primary runtime, so a
            # lean ApplicationHost is read-complete, not just submit-complete. Single-runtime
            # assumption: reads reflect the primary runtime (the lean shapes are
            # single-runtime; see docs/SCOUT-0.51.6-serverctx-foldin.md). ServerContext stays
            # — this is only the read half of the convergence, no surface re-typing.
            wire_standalone_query_bus(self._query_bus, self.runtime())
        self._schema_registry = build_schema_registry()
        service_ctx = HostServiceContext(
            command_bus=self._command_bus,
            query_bus=self._query_bus,
            schemas=self._schema_registry,
            app=self._app,
            event=self._event,
            settings=self.settings,
            resolve_execution_runtime=self._resolve_execution_runtime,
        )
        # Build only the services this app is composed of (+ their transitive deps).
        # Default composition (all_in_one) is full services, so this is behaviour-preserving.
        built = core_service_registry().build_all(service_ctx, only=self.composition.services)
        # Shared product identity (BI-003): assist↔analytics, dashboards, design CQRS.
        bag = apply_product_packaging(
            built,
            command_bus=self._command_bus,
            query_bus=self._query_bus,
            repository=self._app.repository(),
            instance_manager=self._app.instance_manager,
            storage=self._app.storage,
        )
        self._inspect = bag.inspect
        self._session = bag.session
        self._definitions = bag.definitions
        self._execution = bag.execution
        self._assist = bag.assist
        self._design = bag.design
        # 0.67.17: product slot aliases the install organ. Do not keep a twin.
        self._alias_analytics(bag)
        # Host-only packaging: workplane seats (not product service identity).
        self._workplane.wire_start_ports()
        self._workplane.wire_event_journal()
        self._workplane.wire_inbound()

    def _alias_analytics(self, bag: Any) -> None:
        """Bind the product service onto the install organ when DNA lists it.

        ``analytics_enabled`` refines that object. DNA omit drops the host
        slot — composition.services must not keep a twin.
        """
        try:
            install = self.runtime().install
        except Exception:
            install = None
        if not self.admission.has_capability(CAPABILITY_ANALYTICS) or install is None:
            if self._assist is not None:
                self._assist.bind_analytics(None)
            self._analytics = None
            return
        service = bag.analytics
        organ = service if service is not None else install.analytics
        if service is not None:
            install.bind(analytics=service)
        if organ is not None:
            organ.replace_enabled(bool(self.settings.analytics_enabled))
        if self._assist is not None:
            self._assist.bind_analytics(organ)
        self._analytics = organ

    def reload_work_triggers(self) -> int:
        """Reload definition triggers into the work drain (after design/example load)."""
        return self._workplane.reload_work_triggers()

    def reload_inbound_bindings(self) -> int:
        """Rescan resources with metadata.inbound (0.43)."""
        return self._workplane.reload_inbound_bindings()

    def tick_work(self, *, limit: int = 10, schedules: bool = True) -> int:
        """Process due WorkIntents (and optional schedule triggers). Returns count."""
        return self._workplane.tick_work(limit=limit, schedules=schedules)

    @property
    def admission(self) -> Any:
        """Primary runtime admission snapshot (0.63) — fail closed when absent."""
        from palm.core.structure import AdmissionSnapshot

        try:
            return self._app.runtime().admission
        except Exception:
            return AdmissionSnapshot.empty()

    def packaging_status(self) -> dict[str, Any]:
        """Single residual packaging bag (CS-002) — not living seat law.

        Prefer :meth:`~palm.services.inspect.InspectService.top` /
        :meth:`~palm.services.inspect.InspectService.vitality` for living eyes.
        """
        return self._observability.packaging_status()

    def event_plane_status(self) -> dict[str, Any]:
        """Residual bus packaging (CS-002) — prefer packaging_status / inspect top."""
        return self._observability.event_plane_status()

    def ops_status(self) -> dict[str, Any]:
        """Residual ops packaging (CS-002) — prefer packaging_status / inspect top."""
        return self._observability.ops_status()

    def control_plane_status(self) -> dict[str, Any]:
        """Residual work/journal/boot packaging (CS-002) — not living seat law.

        Same body as :meth:`packaging_status`. Prefer that name for new callers.
        """
        return self._observability.control_plane_status()

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError("ApplicationHost is not started; call start() first")

    def _require_business_admission(self) -> None:
        """Host packaging door for business start (0.63.33) — fail closed on admission."""
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self.admission)


def run_host(
    profile: DeploymentProfile | str = "all_in_one",
    *,
    settings: PalmSettings | None = None,
    boot_mode: BootMode | str | None = None,
    **start_options: Any,
) -> None:
    """
    Start an :class:`ApplicationHost`, block on signals, then shut down.

    Library helper for standalone master/worker/server processes.

    **0.63.12:** when *boot_mode* is omitted, deployment roles seed structure
    definition via host spawn (server → ``local.server``, worker → ``local.worker``, …).
    Pass *boot_mode* to pin a BootMode seed explicitly.
    """
    resolved = (
        profile
        if isinstance(profile, DeploymentProfile)
        else DeploymentProfile.from_preset(profile)
    )
    host = ApplicationHost(settings=settings, profile=resolved, boot_mode=boot_mode)
    host.start(**start_options)
    try:
        host.run_until_signal()
    finally:
        host.shutdown()
