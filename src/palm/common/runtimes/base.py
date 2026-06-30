"""
BaseRuntime — shared engine wiring and definition submission surface.

Concrete runtimes (:class:`~palm.runtimes.embedded.runtime.EmbeddedRuntime`,
:class:`~palm.runtimes.daemon.runtime.DaemonRuntime`) differ only in default scheduling
policy and optional runtime-specific conveniences.
"""

from __future__ import annotations

from typing import Any, ClassVar

import palm.patterns  # — register patterns
import palm.providers  # — register providers
import palm.storages  # noqa: F401 — register core backends
from palm import __version__
from palm.common import DefinitionExecutor, DefinitionRepository, InstanceRepository
from palm.common.events import OutboxProcessor, OutboxStore, wire_reliable_events
from palm.common.hooks import InstancePersistenceHook, OutboxDrainHook, StateSnapshotHook
from palm.common.managers import InstanceManager
from palm.common.resource import resource_definition_resolver
from palm.common.runtimes.hooks import (
    AuthMiddleware,
    ChildCompletionHook,
    DriveObservabilityHook,
    JobExecutionContextHook,
    authenticate_runtime,
)
from palm.common.runtimes.schedulers import QueuedScheduler
from palm.common.runtimes.wiring import SchedulerPolicy, resolve_scheduler
from palm.common.storage import StorageFactory
from palm.core import (
    AuthEngine,
    BehaviorTreeEngine,
    ContextEngine,
    EventEngine,
    Job,
    OrchestrationEngine,
    ResourceEngine,
    StorageEngine,
)
from palm.core.context import BaseState
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.instances import ProcessInstance
from palm.states import BlackboardState


class BaseRuntime:
    """
    Coordinates Palm engines and exposes definition-driven job submission.

    Structurally satisfies :class:`~palm.common.runtimes.host.RuntimeHost`. Subclasses
    set :attr:`default_scheduler_policy` to choose inline vs queued driving.
    """

    runtime_name: ClassVar[str] = "Runtime"
    default_scheduler_policy: ClassVar[SchedulerPolicy] = "inline"

    def __init__(
        self,
        *,
        storage: StorageEngine | None = None,
        instance_manager: InstanceManager | None = None,
    ) -> None:
        self.context = ContextEngine()
        self.event = EventEngine()
        self.behavior_tree = BehaviorTreeEngine()
        self.resource = ResourceEngine()
        self.auth = AuthEngine()
        self.orchestration = OrchestrationEngine()
        self._owns_storage = storage is None
        self.storage = storage if storage is not None else StorageEngine()
        self.repository = DefinitionRepository(self.storage)
        if instance_manager is not None:
            self.instance_manager = instance_manager
            self.instances = instance_manager.repository
        else:
            self.instances = InstanceRepository(self.storage)
            self.instance_manager = InstanceManager(self.instances)
        self._owns_instance_manager = instance_manager is None
        self.executor = DefinitionExecutor(self, self.repository, self.instance_manager)
        self._started = False
        self._auth_enforce = False
        self._outbox_store: OutboxStore | None = None
        self._outbox_processor: OutboxProcessor | None = None

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def version(self) -> str:
        return __version__

    @property
    def auth_enforce(self) -> bool:
        """Whether drive authorization is required for job execution."""
        return self._auth_enforce

    @property
    def outbox_store(self) -> OutboxStore | None:
        """Durable outbox store when ``enable_event_outbox`` is active."""
        return self._outbox_store

    @property
    def outbox_processor(self) -> OutboxProcessor | None:
        """Outbox drain helper wired at runtime start."""
        return self._outbox_processor

    def start(self, **options: Any) -> None:
        """Initialize engines, wire orchestration, and begin accepting jobs."""
        if self._started:
            return

        self.context.initialize()
        self.event.initialize()
        cache_options = options.get("resource_cache")
        resource_options: dict[str, Any] = {
            "event_engine": self.event,
            "definition_resolver": resource_definition_resolver(self.repository),
        }
        if cache_options is not None:
            resource_options["resource_cache"] = cache_options
        self.resource.initialize(**resource_options)
        self.auth.initialize()
        authenticate_runtime(self.auth, options.get("credentials"))

        if not self.storage.is_initialized:
            StorageFactory.initialize_engine(
                self.storage,
                storage_backend=str(options.get("storage_backend", "memory")),
                **dict(options.get("backend_options") or {}),
            )

        enable_outbox = bool(options.get("enable_event_outbox", True))
        if enable_outbox:
            self._outbox_store = OutboxStore(self.storage)
            wire_reliable_events(self.event, self._outbox_store)
            self._outbox_processor = OutboxProcessor(self._outbox_store, self.event)

        scheduler = resolve_scheduler(
            options,
            default_policy=self.default_scheduler_policy,
        )
        hooks = list(options.get("hooks") or [])
        if options.get("observability"):
            hooks.append(DriveObservabilityHook())
        self._auth_enforce = bool(options.get("auth_enforce"))
        if self._auth_enforce:
            hooks.append(
                AuthMiddleware(
                    self.auth,
                    required_roles=tuple(options.get("auth_roles") or ("user",)),
                )
            )
        hooks.append(JobExecutionContextHook())
        hooks.append(ChildCompletionHook(self))
        hooks.append(
            InstancePersistenceHook(
                self.instance_manager,
                outbox_store=self._outbox_store,
            )
        )
        if self._outbox_processor is not None:
            hooks.append(OutboxDrainHook(self._outbox_processor))
        if options.get("enable_state_snapshot"):
            hooks.append(
                StateSnapshotHook(
                    self.instance_manager,
                    snapshot_on_status=options.get("snapshot_on_status"),
                    max_snapshots_per_instance=int(options.get("max_snapshots_per_instance", 10)),
                )
            )

        orch_options: dict[str, Any] = {
            "scheduler": scheduler,
            "event_engine": self.event,
            "context_engine": self.context,
            "hooks": hooks,
        }
        max_jobs = options.get("max_concurrent_jobs")
        if isinstance(max_jobs, int) and max_jobs > 0:
            orch_options["max_concurrent_jobs"] = max_jobs
        self.orchestration.initialize(**orch_options)

        state = options.get("state")
        bt_state: BaseState = state if isinstance(state, BaseState) else BlackboardState()
        self.behavior_tree.initialize(state=bt_state)

        if not self.instance_manager.is_initialized:
            self.instance_manager.initialize(
                max_loaded_instances=options.get("max_loaded_instances"),
                max_concurrent_active=options.get("max_concurrent_active"),
                max_snapshots_per_instance=options.get("max_snapshots_per_instance"),
                reconcile_on_startup=options.get("reconcile_on_startup"),
            )

        self.orchestration.start()
        self._started = True

        from palm.providers._registry import get_runtime_binding

        bind_runtime = get_runtime_binding()
        if bind_runtime is not None:
            bind_runtime(self)

    def stop(self) -> None:
        """Stop orchestration and shut down all engines."""
        if not self._started:
            return

        from palm.providers._registry import get_runtime_unbinding

        unbind_runtime = get_runtime_unbinding()
        if unbind_runtime is not None:
            unbind_runtime()

        self.orchestration.stop()
        if self._owns_instance_manager:
            self.instance_manager.shutdown()
        if self._owns_storage:
            self.storage.shutdown()
        self.orchestration.shutdown()
        self.behavior_tree.shutdown()
        self.resource.shutdown()
        self.auth.shutdown()
        self.context.shutdown()
        self.event.shutdown()
        self._started = False

    def submit_flow(
        self,
        flow: FlowDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: BlackboardState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Submit a flow definition or repository name/id as an orchestration job."""
        if isinstance(flow, FlowDefinition):
            return self.executor.submit_flow(
                flow,
                job_id=job_id,
                state=state,
                metadata=metadata,
            )
        return self.executor.submit_flow(
            flow,
            by_id=by_id,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def submit_process(
        self,
        process: ProcessDefinition | str,
        *,
        by_id: bool = False,
        job_id: str | None = None,
        state: BlackboardState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job | list[Job]:
        """Submit a process definition or repository reference."""
        if isinstance(process, ProcessDefinition):
            jobs = self.executor.submit_process(
                process,
                job_id=job_id,
                state=state,
                metadata=metadata,
            )
        else:
            jobs = self.executor.submit_process(
                process,
                by_id=by_id,
                job_id=job_id,
                state=state,
                metadata=metadata,
            )
        return jobs[0] if len(jobs) == 1 else jobs

    def submit_wizard(
        self,
        *,
        name: str = "wizard",
        config: object | None = None,
        steps: int | None = None,
        job_id: str | None = None,
        state: BlackboardState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Submit an interactive wizard via the executions builder."""
        options: dict[str, Any] = {}
        if config is not None:
            options["config"] = config
        if steps is not None:
            options["steps"] = steps
        flow = FlowDefinition(name=name, pattern="wizard", options=options)
        meta = dict(metadata or {})
        meta.setdefault("pattern", "wizard")
        return self.submit_flow(flow, job_id=job_id, state=state, metadata=meta)

    def provide_input(self, job_id: str, value: Any) -> str | None:
        """Provide input for a waiting interactive job and resume execution."""
        self._require_started()
        return self.orchestration.deliver_input(job_id, value)

    def resume_process(self, instance_id: str) -> Job:
        """Resume a persisted process instance."""
        self._require_started()
        return self.executor.resume_process(instance_id)

    def get_instance(self, instance_id: str) -> ProcessInstance:
        """Load a persisted process instance record."""
        self._require_started()
        return self.instance_manager.get(instance_id)

    def get_job(self, job_id: str) -> Job:
        """Return a registered orchestration job."""
        self._require_started()
        return self.orchestration.get_job(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a non-terminal job."""
        self._require_started()
        return self.orchestration.cancel_job(job_id)

    def current_wizard_step(self, job_id: str) -> str | None:
        """Return the active step slug when the job executable supports inspection."""
        self._require_started()
        return self.orchestration.inspect_step(job_id)

    def wizard_answers(self, job_id: str) -> dict[str, Any]:
        """Return collected answers when the job executable supports inspection."""
        self._require_started()
        return self.orchestration.inspect_answers(job_id)

    def wait_until_idle(self, *, timeout: float = 5.0) -> bool:
        """
        Block until a queued scheduler has processed pending work.

        No-op for inline schedulers. Useful for tests and coordinated shutdown
        of background runtimes (:class:`~palm.runtimes.daemon.runtime.DaemonRuntime`,
        :class:`~palm.runtimes.server.runtime.ServerRuntime`).
        """
        self._require_started()
        scheduler = self.orchestration.scheduler
        if isinstance(scheduler, QueuedScheduler):
            return scheduler.wait_until_idle(timeout=timeout)
        return True

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError(f"{self.runtime_name} is not started; call start() first")
