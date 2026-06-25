"""
ApplicationHost — top-level Palm orchestrator with CQRS command/query routing.
"""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Any, Self

from palm.app.app import PalmApp
from palm.app.bootstrap import host_profile_from_settings, runtime_start_options
from palm.app.host.cqrs_wiring import wire_command_bus, wire_query_bus
from palm.app.host.event_recorder import HostEventRecorder, RecordedEvent
from palm.app.host.events import HostEventType
from palm.app.host.outbox_service import OutboxBackgroundService
from palm.app.host.roles import HostProfile
from palm.app.host.router import RuntimeRouter
from palm.app.host.workers import WorkerCoordinator
from palm.app.settings import PalmSettings
from palm.common.compensation import (
    CompensationCoordinator,
    default_compensation_registry,
)
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
from palm.patterns._registry import get_projection_factory, registered_projection_factories
from palm.patterns.wizard.bindings.cqrs.projection import (
    WizardProgressProjection,
    WizardProgressReadModel,
)
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    ListWizardProgressQuery,
)
from palm.common.cqrs.rebuild import ProjectionRebuildPolicy
from palm.common.events.external import WebhookDispatcher, webhook_targets_from_urls
from palm.core.event import EventEngine
from palm.core.storage import StorageEngine

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.core.orchestration import Job
    from palm.core.resource import ProviderResult
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition


class ApplicationHost:
    """
    Top-level Palm orchestrator — roles, CQRS, projections, and recovery.

    :class:`~palm.app.app.PalmApp` remains the infrastructure layer (shared
    storage, runtime registry). The host owns command dispatch, query serving,
    worker routing, and background services::

        host = ApplicationHost(profile=HostProfile.all_in_one())
        host.start()
        job = host.execute(SubmitFlowCommand(flow="my_flow"))
        rows = host.ask(ListInstancesQuery(include_terminal=False))
        host.shutdown()
    """

    def __init__(
        self,
        settings: PalmSettings | None = None,
        *,
        profile: HostProfile | None = None,
        storage: StorageEngine | None = None,
    ) -> None:
        self.settings = settings or PalmSettings()
        self.profile = profile or host_profile_from_settings(self.settings)
        self._app = PalmApp(self.settings, storage=storage)
        self._event = EventEngine()
        self._command_bus = CommandBus()
        self._query_bus = QueryBus()
        self._router = RuntimeRouter(self._app)
        self._projection_manager = ProjectionManager()
        self._instance_projection: InstanceIndexProjection | None = None
        self._pattern_projections: dict[str, Any] = {}
        self._resource_projection: ResourceInvocationProjection | None = None
        self._job_board_projection: JobStatusBoardProjection | None = None
        self._outbox_service: OutboxBackgroundService | None = None
        self._compensation: CompensationCoordinator | None = None
        self._worker_coordinator: WorkerCoordinator | None = None
        self._webhook_dispatcher: WebhookDispatcher | None = None
        self._event_recorder = HostEventRecorder()
        self._last_recovery: dict[str, Any] | None = None
        self._started = False
        self._signal_stop = threading.Event()

    @property
    def app(self) -> PalmApp:
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
    def router(self) -> RuntimeRouter:
        return self._router

    @property
    def projections(self) -> ProjectionManager:
        return self._projection_manager

    @property
    def instance_projection(self) -> InstanceIndexProjection | None:
        return self._instance_projection

    @property
    def wizard_projection(self) -> WizardProgressProjection | None:
        projection = self._pattern_projections.get("wizard")
        return projection if isinstance(projection, WizardProgressProjection) else None

    def pattern_projection(self, name: str) -> Any | None:
        return self._pattern_projections.get(name)

    @property
    def resource_projection(self) -> ResourceInvocationProjection | None:
        return self._resource_projection

    @property
    def job_board_projection(self) -> JobStatusBoardProjection | None:
        return self._job_board_projection

    @property
    def outbox_service(self) -> OutboxBackgroundService | None:
        return self._outbox_service

    @property
    def compensation(self) -> CompensationCoordinator | None:
        return self._compensation

    @property
    def compensation_registry(self):
        return default_compensation_registry()

    @property
    def webhook_dispatcher(self) -> WebhookDispatcher | None:
        return self._webhook_dispatcher

    @property
    def event_recorder(self) -> HostEventRecorder:
        return self._event_recorder

    @property
    def last_recovery(self) -> dict[str, Any] | None:
        return self._last_recovery

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
        self._spawn_runtimes(merged)
        self._app.load_definitions()
        self._wire_cqrs()
        self._start_server_surface()
        self._attach_projections()
        self._recover()

        self._event.emit(
            HostEventType.STARTED,
            roles=sorted(self.profile.roles),
            primary=self._app.primary_name,
        )
        self._started = True
        return self

    def shutdown(self) -> None:
        """Stop services, projections, and all runtimes."""
        if not self._started:
            return

        if self._outbox_service is not None:
            self._outbox_service.stop()
            self._outbox_service = None

        if self._compensation is not None:
            self._compensation.shutdown()
            self._compensation = None

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

    def _wire_cqrs(self) -> None:
        import palm.patterns  # noqa: F401 — ensure pattern projection factories are registered

        self._instance_projection = InstanceIndexProjection(
            self._app.storage,
            self._app.instance_manager,
        )
        self._resource_projection = ResourceInvocationProjection(self._app.storage)
        self._job_board_projection = JobStatusBoardProjection(self._app.storage)
        self._pattern_projections = {}
        for pattern_name in registered_projection_factories():
            factory = get_projection_factory(pattern_name)
            if factory is not None:
                self._pattern_projections[pattern_name] = factory(self._app.storage)
        self._projection_manager.register(self._instance_projection)
        for projection in self._pattern_projections.values():
            self._projection_manager.register(projection)
        self._projection_manager.register(self._resource_projection)
        self._projection_manager.register(self._job_board_projection)
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

    def _attach_projections(self) -> None:
        self._projection_manager.attach(self._event)
        self._projection_manager.attach_runtimes(self._app)

    def _recover(self) -> None:
        recovery: dict[str, Any] = {}

        coordinator = self._worker_coordinator or WorkerCoordinator(self.profile, self._event)
        self._worker_coordinator = coordinator
        workers_ready = coordinator.wait_until_ready(
            self._app,
            timeout=self.settings.worker_ready_timeout,
        )
        recovery["workers_ready"] = workers_ready
        recovery["workers"] = list(coordinator.registered_workers)

        if self.settings.enable_compensation:
            self._compensation = CompensationCoordinator(
                default_compensation_registry(),
                self._event,
            )
            self._compensation.attach(self._event)
            self._compensation.attach_runtimes(self._app)

        if self.profile.master and self.profile.enable_outbox_service:
            self._start_outbox_service()
            if self._outbox_service is not None:
                recovery["outbox_pending"] = self._outbox_service.store.pending_count()

        if self.settings.rebuild_projections_on_startup:
            report = self._projection_manager.rebuild_all(
                policy=ProjectionRebuildPolicy(
                    batch_size=self.settings.projection_rebuild_batch_size,
                    max_instances=self.settings.projection_rebuild_max_instances,
                    skip_if_fresh=self.settings.projection_rebuild_skip_if_fresh,
                )
            )
            recovery["projections"] = report.to_dict()

        if recovery:
            self._last_recovery = dict(recovery)
            self._event.emit(HostEventType.RECOVERED, **recovery)

    def _spawn_runtimes(self, merged: dict[str, Any]) -> None:
        profile = self.profile
        has_primary = False

        if profile.uses_collapsed_runtime:
            runtime = self._app.create_runtime(
                "embedded",
                name="main",
                autostart=True,
                set_primary=True,
                **self._command_options(merged),
            )
            self._emit_runtime_registered("main", "embedded", runtime)
            return

        if profile.master:
            runtime = self._app.create_runtime(
                "embedded",
                name="command",
                autostart=True,
                set_primary=not has_primary,
                **self._command_options(merged),
            )
            has_primary = True
            self._emit_runtime_registered("command", "embedded", runtime)

        if profile.worker and not profile.server:
            for index in range(profile.worker_count):
                name = "worker" if index == 0 else f"worker-{index}"
                runtime = self._app.create_runtime(
                    "daemon",
                    name=name,
                    autostart=True,
                    set_primary=not has_primary,
                    **self._worker_options(merged),
                )
                has_primary = True
                self._emit_runtime_registered(name, "daemon", runtime)

        if profile.server:
            options = self._worker_options(merged)
            options["http"] = False
            runtime = self._app.create_runtime(
                "server",
                name="server",
                autostart=True,
                set_primary=not has_primary,
                host=profile.server_host,
                port=profile.server_port,
                **options,
            )
            self._emit_runtime_registered("server", "server", runtime)

    def _command_options(self, merged: dict[str, Any]) -> dict[str, Any]:
        options = dict(merged)
        options.setdefault("scheduler", "inline")
        return options

    def _worker_options(self, merged: dict[str, Any]) -> dict[str, Any]:
        options = dict(merged)
        options["scheduler"] = "queued"
        return options

    def _start_outbox_service(self) -> None:
        if not self._app.storage.is_initialized:
            return
        dispatcher = self._build_webhook_dispatcher()
        self._outbox_service = OutboxBackgroundService(
            self._app.storage,
            self._event,
            poll_interval=self.profile.outbox_poll_interval,
            external_dispatcher=dispatcher,
        )
        self._outbox_service.start(recover=self.profile.outbox_recover_on_startup)

    def _build_webhook_dispatcher(self) -> WebhookDispatcher | None:
        if not self.settings.enable_webhook_dispatcher:
            return None
        if not self.settings.webhook_urls:
            return None
        self._webhook_dispatcher = WebhookDispatcher(
            webhook_targets_from_urls(
                self.settings.webhook_urls,
                event_types=self.settings.webhook_event_types or None,
            )
        )
        return self._webhook_dispatcher

    def _emit_runtime_registered(self, name: str, kind: str, runtime: BaseRuntime) -> None:
        if self._worker_coordinator is not None:
            self._worker_coordinator.note_runtime(name, kind)
        self._event.emit(
            HostEventType.RUNTIME_REGISTERED,
            name=name,
            kind=kind,
            scheduler=runtime.orchestration.scheduler.__class__.__name__,
        )

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError("ApplicationHost is not started; call start() first")


def run_host(
    profile: HostProfile | str = "all_in_one",
    *,
    settings: PalmSettings | None = None,
    **start_options: Any,
) -> None:
    """
    Start an :class:`ApplicationHost`, block on signals, then shut down.

    Library helper for standalone master/worker/server processes.
    """
    resolved = profile if isinstance(profile, HostProfile) else HostProfile.from_preset(profile)
    host = ApplicationHost(settings=settings, profile=resolved)
    host.start(**start_options)
    try:
        host.run_until_signal()
    finally:
        host.shutdown()
