"""
ApplicationHost — top-level Palm orchestrator with CQRS command/query routing.
"""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Any, Self

from palm.app.bootstrap import deployment_profile_from_settings, runtime_start_options
from palm.app.host.event_recorder import HostEventRecorder, RecordedEvent
from palm.app.host.events import HostEventType
from palm.app.host.lifecycle import RecoveryCoordinator, RuntimeSpawner
from palm.app.host.observability import HostObservability
from palm.app.host.outbox_service import OutboxBackgroundService
from palm.app.host.roles import DeploymentProfile
from palm.app.host.router import RuntimeRouter
from palm.app.host.services import HostServiceContext, core_service_registry
from palm.app.host.wiring import (
    build_host_projections,
    register_host_projections,
    wire_command_bus,
    wire_query_bus,
)
from palm.app.host.workers import WorkerCoordinator
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
from palm.patterns.wizard.bindings.cqrs.projection import (
    WizardProgressReadModel,
)
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    ListWizardProgressQuery,
)
from palm.services._cqrs_wiring import wire_all_service_cqrs
from palm.services.design.contributors import wire_builtin_design_contributors

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.core.orchestration import Job
    from palm.core.resource import ProviderResult
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition


class ApplicationHost:
    """
    Top-level Palm orchestrator — roles, CQRS, projections, and recovery.

    :class:`~palm.app.kernel.PalmKernel` remains the infrastructure layer (shared
    storage, runtime registry). The host owns command dispatch, query serving,
    worker routing, and background services::

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
        storage: StorageEngine | None = None,
    ) -> None:
        self.settings = settings or PalmSettings()
        self.profile = profile or deployment_profile_from_settings(self.settings)
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
        self._worker_coordinator: WorkerCoordinator | None = None
        self._event_recorder = HostEventRecorder()
        self._schema_registry: Any | None = None
        self._system: Any | None = None
        self._definitions: Any | None = None
        self._execution: Any | None = None
        self._assist: Any | None = None
        self._design: Any | None = None
        self._analytics: Any | None = None
        self._started = False
        self._signal_stop = threading.Event()
        self._observability = HostObservability(self)
        self._workplane = WorkPlaneCoordinator(self)
        self._spawner = RuntimeSpawner(self)
        self._recovery = RecoveryCoordinator(self)

    @property
    def app(self) -> PalmKernel:
        """Infrastructure layer — storage and runtime registry."""
        return self._app

    @property
    def event(self) -> EventEngine:
        """Host-level coordination bus."""
        return self._event

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
    def system(self):
        """Operational inspect/debug service API."""
        return self._system

    @property
    def definitions(self):
        """Definition catalog service API."""
        return self._definitions

    @property
    def execution(self):
        """Execution service API (flows, providers, processes)."""
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
        """Analytics service API — BI describe/query (0.35)."""
        return self._analytics

    @property
    def work_drain(self):
        """WorkIntent drain (0.37) — run-when-able deferred flows."""
        return self._workplane.work_drain

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
    def outbox_service(self) -> OutboxBackgroundService | None:
        return self._recovery.outbox_service

    @property
    def webhook_dispatcher(self) -> WebhookDispatcher | None:
        return self._recovery.webhook_dispatcher

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

    def start(self, **options: Any) -> Self:
        """Bootstrap, spawn role runtimes, wire CQRS, and recover state."""
        if self._started:
            return self

        self._app.bootstrap()
        self._event.initialize()
        self._event_recorder.attach(self._event)
        self._worker_coordinator = WorkerCoordinator(self.profile, self._event)
        merged = runtime_start_options(self.settings, **options)
        self._spawner.spawn_runtimes(merged)
        self._app.load_definitions()
        self._wire_cqrs()
        self._start_server_surface()
        self._attach_projections()
        self._recovery.recover()

        self._event.emit(
            HostEventType.STARTED,
            roles=sorted(self.profile.roles),
            primary=self._app.primary_name,
        )
        self._started = True
        if self._work_drain_background_enabled():
            self._workplane.start_background()
        return self

    def _work_drain_background_enabled(self) -> bool:
        """True when continuous WorkIntent drain should run (settings or host profile)."""
        return bool(
            self.settings.enable_work_drain_service or self.profile.enable_work_drain_service
        )

    def shutdown(self) -> None:
        """Stop services, projections, and all runtimes."""
        if not self._started:
            return

        self._workplane.stop_background()
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
        """Invoke a resource definition or direct provider on the host runtime."""
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
    ) -> Job:
        return self.execute(
            SubmitFlowCommand(
                flow=ref,
                runtime_name=runtime_name,
                by_id=by_id,
                job_id=job_id,
                state=state,
                metadata=dict(metadata or {}),
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
        return self.execute(
            ProvideInputCommand(
                job_id=job_id,
                value=value,
                runtime_name=runtime_name,
            )
        )

    def resume_process(self, instance_id: str, *, runtime_name: str | None = None) -> Job:
        return self.execute(
            ResumeProcessCommand(
                instance_id=instance_id,
                runtime_name=runtime_name,
            )
        )

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
        projections = build_host_projections(self._app.storage, self._app.instance_manager)
        register_host_projections(self._projection_manager, projections)
        self._instance_projection = projections.instance
        self._resource_projection = projections.resource
        self._job_board_projection = projections.job_board
        self._pattern_projections = projections.patterns
        wire_command_bus(self._command_bus, self._app, self._router)
        wire_query_bus(
            self._query_bus,
            app=self._app,
            instances=self._instance_projection,
            pattern_projections=self._pattern_projections,
            resource_invocations=self._resource_projection,
            job_board=self._job_board_projection,
            instance_manager=self._app.instance_manager,
        )
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
        built = core_service_registry().build_all(service_ctx)
        self._system = built["system"]
        self._definitions = built["definitions"]
        self._execution = built["execution"]
        self._assist = built["assist"]
        self._design = built["design"]
        self._analytics = built["analytics"]
        self._assist.bind_analytics(self._analytics)
        self._wire_dashboard_store()
        self._workplane.wire_work_drain()
        self._workplane.wire_event_journal()
        self._workplane.wire_inbound()
        wire_builtin_design_contributors()
        wire_all_service_cqrs(
            self._command_bus,
            self._query_bus,
            repository=self._app.repository(),
            instance_manager=self._app.instance_manager,
            design=self._design,
        )

    def _attach_projections(self) -> None:
        self._projection_manager.attach(self._event)
        self._projection_manager.attach_runtimes(self._app)

    def _wire_dashboard_store(self) -> None:
        """0.41 — durable dashboard definitions on host storage."""
        if not self._app.storage.is_initialized:
            return
        from palm.services.analytics.dashboards import attach_dashboard_store

        attach_dashboard_store(self._app.storage)

    def reload_work_triggers(self) -> int:
        """Reload definition triggers into the work drain (after design/example load)."""
        return self._workplane.reload_work_triggers()

    def reload_inbound_bindings(self) -> int:
        """Rescan resources with metadata.inbound (0.43)."""
        return self._workplane.reload_inbound_bindings()

    def tick_work(self, *, limit: int = 10, schedules: bool = True) -> int:
        """Process due WorkIntents (and optional schedule triggers). Returns count."""
        return self._workplane.tick_work(limit=limit, schedules=schedules)

    def event_plane_status(self) -> dict[str, Any]:
        """Which EventEngine each reactive surface uses (0.45.5 doctor contract)."""
        return self._observability.event_plane_status()

    def ops_status(self) -> dict[str, Any]:
        """Operator ergonomics — invoke routes, storage, event-log durability (0.45.8)."""
        return self._observability.ops_status()

    def control_plane_status(self) -> dict[str, Any]:
        """Pending work + journal lag for doctor/ops (0.38 / 0.40.3)."""
        return self._observability.control_plane_status()

    def drain_journal_webhooks(self, *, limit: int = 50, on_entry: Any | None = None) -> int:
        """Catch-up webhooks consumer from journal (0.40.3). Returns entries processed."""
        return self._workplane.drain_journal_webhooks(limit=limit, on_entry=on_entry)

    def drain_journal_projections(self, *, limit: int = 50, on_entry: Any | None = None) -> int:
        """Catch-up projections consumer from journal (0.40.3)."""
        return self._workplane.drain_journal_projections(limit=limit, on_entry=on_entry)

    def redrive_journal(
        self,
        *,
        from_offset: int = 0,
        to_offset: int | None = None,
        event_types: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Replay journal entries for operator tooling (does not move consumer offsets)."""
        return self._workplane.redrive_journal(
            from_offset=from_offset,
            to_offset=to_offset,
            event_types=event_types,
            limit=limit,
        )

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError("ApplicationHost is not started; call start() first")


def run_host(
    profile: DeploymentProfile | str = "all_in_one",
    *,
    settings: PalmSettings | None = None,
    **start_options: Any,
) -> None:
    """
    Start an :class:`ApplicationHost`, block on signals, then shut down.

    Library helper for standalone master/worker/server processes.
    """
    resolved = profile if isinstance(profile, DeploymentProfile) else DeploymentProfile.from_preset(profile)
    host = ApplicationHost(settings=settings, profile=resolved)
    host.start(**start_options)
    try:
        host.run_until_signal()
    finally:
        host.shutdown()
