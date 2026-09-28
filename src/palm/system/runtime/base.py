"""
BaseRuntime — concrete **system instance** for a running Palm.

Holds engines, planes, and the :class:`~palm.system.interfaces.execution.ExecutionPort`
surface for graphs and product. Canonical home: :mod:`palm.system.runtime`.


Concrete surfaces (:class:`~palm.runtimes.embedded.runtime.EmbeddedRuntime`,
:class:`~palm.runtimes.daemon.runtime.DaemonRuntime`) differ only in default scheduling
policy and optional runtime-specific conveniences.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from palm import __version__
from palm.common import DefinitionRepository, InstanceRepository
from palm.common.events import OutboxProcessor, OutboxStore
from palm.common.managers import InstanceManager
from palm.common.providers._registry import get_runtime_unbinding
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
from palm.core.structure import CAPABILITY_WORK_DRAIN, AdmissionSnapshot
from palm.core.workload import WorkloadEngine
from palm.core.workload.owner import WorkloadOwner
from palm.core.workload.spec import WorkloadSpec
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.instances import ProcessInstance
from palm.states import BlackboardState
from palm.system.boot import (
    SYSTEM_PHASES,
    BootContext,
    build_system_handlers,
    walk_schedule,
)
from palm.system.bound import BOUND_DRIVERS_VERSION, BoundDrivers
from palm.system.executions import DefinitionExecutor
from palm.system.interfaces.install import SystemInstall
from palm.system.log import get_system_log
from palm.system.runtime.schedulers import QueuedScheduler
from palm.system.runtime.wiring import SchedulerPolicy
from palm.system.structure.seat import StructureSeat
from palm.system.subsystems.planes.hub import SystemPlanes
from palm.system.subsystems.planes.session.plane import SessionPlaneService
from palm.system.subsystems.planes.wait.plane import WaitPlaneService

if TYPE_CHECKING:
    from palm.system.interfaces.execution import ExecutionPort


class BaseRuntime:
    """
    System instance shell: engines, planes, effect ports.

    **Start law lives in** ``palm.system.boot`` (0.59.3+). This class holds the
    machine; ``start()`` walks the system phase table. Do not grow private boot
    order here — add or migrate a phase handler under boot.

    Satisfies :class:`~palm.system.instance.SystemInstance` and
    :class:`~palm.system.interfaces.execution.ExecutionPort` structurally.
    Also satisfies the thin legacy :class:`~palm.system.runtime.host.RuntimeHost`.

    Subclasses set :attr:`default_scheduler_policy` to choose inline vs queued driving.
    Prefer ``runtime.execution`` for resource/workload effects (0.57+), not edge
    field access to engines.
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
        self.workload = WorkloadEngine()
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
        self._planes: SystemPlanes | None = None
        self._supervisor: Any | None = None
        self._install = SystemInstall()
        self._structure: StructureSeat | None = None
        self._last_boot_walk: list[Any] | None = None
        self._start_options: dict[str, Any] = {}
        self.application_host: Any | None = None

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def execution(self) -> ExecutionPort:
        """Effect interface shared by graphs and product (resource + workload)."""
        return self

    @property
    def install(self) -> SystemInstall:
        """
        Collaborator install interface (peer of :attr:`execution`).

        Boot binds named ports via :meth:`bind_system_install`. Plane and
        supervisor install read this seat — they do not dig the bag.
        """
        return self._install

    @property
    def structure(self) -> StructureSeat | None:
        """Structure seat (definition + engine + admission) after structure assemble."""
        return self._structure

    @structure.setter
    def structure(self, seat: StructureSeat | None) -> None:
        self._structure = seat

    @property
    def admission(self) -> AdmissionSnapshot:
        """Published gate: may business that needs ground run?

        Fail closed when structure assemble has not run or is not ready.
        """
        if self._structure is None:
            return AdmissionSnapshot.empty()
        return self._structure.admission()

    @property
    def wire(self) -> SystemInstall:
        """Alias of :attr:`install` (temporary; prefer ``install``)."""
        return self._install

    @property
    def version(self) -> str:
        return __version__

    @property
    def auth_enforce(self) -> bool:
        """Whether drive authorization is required for job execution."""
        return self._auth_enforce

    @property
    def outbox_store(self) -> OutboxStore | None:
        """Durable outbox store when DNA lists ``outbox``."""
        return self._outbox_store

    @property
    def outbox_processor(self) -> OutboxProcessor | None:
        """Outbox drain helper wired at runtime start."""
        return self._outbox_processor

    @property
    def planes(self) -> SystemPlanes | None:
        """Planes hub — consumes wait/session/work (0.61). ``None`` before attach."""
        return self._planes

    @property
    def wait_plane(self) -> WaitPlaneService | None:
        """Continue plane — from :attr:`planes` hub, or ``None``."""
        hub = self._planes
        return None if hub is None else hub.get("wait")  # type: ignore[return-value]

    @property
    def wait_matcher(self) -> Any:
        """Matcher inside the continue plane (0.55.4+), or ``None``."""
        plane = self.wait_plane
        return None if plane is None else plane.matcher

    @property
    def session_plane(self) -> SessionPlaneService | None:
        """Session plane — from :attr:`planes` hub, or ``None``."""
        hub = self._planes
        return None if hub is None else hub.get("session")  # type: ignore[return-value]

    @property
    def work_plane(self) -> Any | None:
        """Start plane — from :attr:`planes` hub, or ``None``."""
        hub = self._planes
        return None if hub is None else hub.get("work")

    def plane(self, name: str) -> Any | None:
        """Plane by hub name (``wait``) or alias (``wait_plane``)."""
        hub = self._planes
        return None if hub is None else hub.get(name)

    @property
    def supervisor(self) -> Any | None:
        """Continuous system services supervisor (0.60), or ``None`` before wire."""
        return self._supervisor

    def bind_system_install(self) -> SystemInstall:
        """
        Explicitly bind engine collaborators onto :attr:`install`.

        Call after engines/storage/orchestration exist (boot phase
        ``system.install.bind``). Re-call after planes attach to publish
        ``work_plane`` for the supervisor.
        """

        def _get_job(job_id: str) -> Any:
            return self.get_job(str(job_id))

        def _submit(
            flow_id: str,
            metadata: dict[str, Any] | None = None,
            state: Any = None,
        ) -> Any:
            return self.submit_flow(flow_id, metadata=metadata, state=state)

        def _able() -> bool:
            """Started and organism-ready. Wait / continue uses this query.

            Live check: structure assemble may complete after planes attach.
            """
            if not self._started:
                return False
            return bool(self.admission.may_run_business)

        def _drain_able() -> bool:
            """Work-plane start port: ready **and** ``work_drain`` installed.

            0.67.2 — ready is not membership. Host spawn may inject
            ``install_able`` (drain) and ``install_admission_able`` (ready).
            """
            if not _able():
                return False
            return bool(self.admission.has_capability(CAPABILITY_WORK_DRAIN))

        opts = self._start_options
        submit = opts.get("install_submit") or _submit
        override = opts.get("install_able")
        admission_override = opts.get("install_admission_able")
        able = override or _drain_able
        admission_able = admission_override or _able
        self._install.bind(
            orchestration=self.orchestration,
            event=self.event,
            storage=self.storage,
            instance_manager=self.instance_manager,
            get_job=_get_job,
            submit=submit,
            able=able,
            admission_able=admission_able,
            outbox_store=self._outbox_store,
            outbox_processor=self._outbox_processor,
            work_plane=self.work_plane,
        )
        return self._install

    def bind_system_wire(self) -> SystemInstall:
        """Alias of :meth:`bind_system_install` (temporary)."""
        return self.bind_system_install()

    @property
    def last_boot_walk(self) -> list[Any] | None:
        """Last system boot walk results (0.59+), or ``None`` before start.

        Vitality / membership observation reads this seat. Prefer this property
        over the private ``_last_boot_walk`` field.
        """
        return self._last_boot_walk

    def start(self, **options: Any) -> None:
        """Hand control to the system boot schedule (``SYSTEM_PHASES``).

        0.59.3 — no private soup here. Rules live in
        ``palm.system.boot.system_schedule``. Observation via SystemLog.

        0.72.5 — this schedule does not install packages. The bundle installs
        before it calls ``start``.

        0.72.6 — ``drivers`` is a :class:`~palm.system.bound.BoundDrivers` value.
        This schedule attaches that storage. It does not choose a storage or a
        workload runtime.
        """
        refused = [key for key in ("plugin_install", "composition_packages") if key in options]
        if refused:
            names = ", ".join(refused)
            raise RuntimeError(f"system start does not install packages; refused {names}")
        if self._started:
            return
        slot_keys = [
            key
            for key in ("storage_backend", "backend_options", "workload_default_runtime")
            if key in options
        ]
        if slot_keys:
            names = ", ".join(slot_keys)
            raise RuntimeError(f"system start takes bound drivers; refused {names}")
        drivers = options.get("drivers")
        if not isinstance(drivers, BoundDrivers):
            raise RuntimeError("system start requires bound drivers")
        if drivers.version != BOUND_DRIVERS_VERSION:
            raise RuntimeError(
                f"bound drivers contract version {drivers.version} is not {BOUND_DRIVERS_VERSION}"
            )
        if not drivers.storage.is_open:
            raise RuntimeError("bound storage is not initialized")

        self._start_options = dict(options)
        slog = get_system_log()
        runtime = getattr(self, "name", None) or self.runtime_name
        ctx = BootContext(
            schedule="system",
            runtime=str(runtime),
            shell=self,
        )
        slog.info(
            "boot.start",
            "system schedule start",
            schedule="system",
            runtime=str(runtime),
        )
        try:
            # Boot owns order + handlers; this shell is the structure target.
            self._last_boot_walk = walk_schedule(
                SYSTEM_PHASES,
                build_system_handlers(self, options),
                ctx=ctx,
                log=slog,
                require_handlers=True,
            )
        except Exception as exc:
            slog.emit(
                1,
                "boot.fail",
                f"system boot fail: {type(exc).__name__}: {exc}",
                schedule="system",
                runtime=str(runtime),
                reason=f"{type(exc).__name__}: {exc}",
            )
            raise

    def stop(self) -> None:
        """Stop orchestration and shut down all engines."""
        if not self._started:
            return

        slog = get_system_log()
        runtime = getattr(self, "name", None) or self.runtime_name
        slog.info(
            "shutdown.start",
            "system shutdown start",
            schedule="system",
            runtime=str(runtime),
        )

        unbind_runtime = get_runtime_unbinding()
        if unbind_runtime is not None:
            unbind_runtime()

        if self._supervisor is not None:
            try:
                self._supervisor.stop()
            except Exception:
                pass
            self._supervisor = None

        if self._structure is not None:
            try:
                self._structure.reset()
            except Exception:
                pass
            self._structure = None

        if self._planes is not None:
            try:
                self._planes.detach()
            except Exception:
                pass
            self._planes = None

        self.orchestration.stop()
        if self._owns_instance_manager:
            self.instance_manager.shutdown()
        if self._owns_storage:
            self.storage.shutdown()
        self.orchestration.shutdown()
        self.behavior_tree.shutdown()
        if self.workload.is_initialized:
            self.workload.shutdown()
        self.resource.shutdown()
        self.auth.shutdown()
        self.context.shutdown()
        self.event.shutdown()
        self._started = False
        slog.info(
            "shutdown.end",
            "system shutdown end",
            schedule="system",
            runtime=str(runtime),
        )

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
        """Provide input for a waiting interactive job and resume execution.

        **0.63.25:** product continue through the shell requires
        admission (same law as submit / resume_job). Wait-plane deliver that
        drives orchestration directly is a named residual (not this door).
        """
        from palm.system.structure.errors import require_business_admission

        self._require_started()
        require_business_admission(self)
        return self.orchestration.deliver_input(job_id, value)

    def resume_process(self, instance_id: str) -> Job:
        """Resume a persisted process instance (product continue).

        **0.63.29 cartography:** fail closed under admission. Enforcement is
        on ``DefinitionExecutor.resume_process`` via ``_require_runtime``
        (same gate as submit since 0.63.4); shell documents the product-continue door.
        """
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
        """Cancel a non-terminal job — control path (not an admission-gated business path).

        **0.63.30 named residual:** remains available when admission is closed
        so operators and shutdown can stop work (same spirit as stop_workload).
        """
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

    # --- ExecutionPort (system effect surface) --------------------------------

    def invoke_resource(
        self,
        resource_ref: str | None = None,
        *,
        provider: str | None = None,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        state: Any = None,
        resource_id: str | None = None,
        correlation: dict[str, Any] | None = None,
    ) -> Any:
        """Invoke a resource via the resource engine (ExecutionPort).

        **0.63.24:** product / graph resource effects through this port
        require admission (same law as submit_flow / start_workload). Direct
        ``ResourceEngine.invoke`` remains available for unit / place-registry paths
        that are not product business doors.
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self)
        engine = self.resource
        if not engine.is_initialized:
            engine.initialize()
        return engine.invoke(
            resource_ref,
            provider=provider,
            action=action,
            params=params,
            state=state,
            resource_id=resource_id,
            correlation=correlation,
        )

    def start_workload(
        self,
        spec: Any,
        *,
        owner: Any = None,
        workload_id: str | None = None,
        idempotency_key: str | None = None,
        host_id: str | None = None,
    ) -> Any:
        """Start a workload via the workload engine (ExecutionPort).

        **0.63.20:** product / graph start through this port requires
        admission (same law as submit_flow). Structure assemble / place-registry spawn uses
        ``WorkloadEngine`` directly and is not forced through this door.
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self)
        engine = self._require_workload_engine()
        parsed = spec if isinstance(spec, WorkloadSpec) else WorkloadSpec.from_dict(dict(spec))
        bound_owner = _coerce_workload_owner(owner)
        # 0.58.8 — fill session/job/instance from event context when job path has them
        bound_owner = _enrich_workload_owner_from_event_context(self, bound_owner)
        return engine.start(
            parsed,
            owner=bound_owner,
            workload_id=workload_id,
            idempotency_key=idempotency_key,
            host_id=host_id,
        )

    def exec_workload(
        self,
        workload_id: str,
        command: list[str] | tuple[str, ...],
        *,
        timeout_s: float | None = None,
        env: dict[str, str] | None = None,
    ) -> Any:
        """Exec argv on a READY workload (ExecutionPort).

        **0.63.27:** product / graph exec through this port requires
        admission (same law as start_workload). Direct ``WorkloadEngine.exec``
        remains ungated for unit / non-port paths (named residual).
        """
        from palm.system.structure.errors import require_business_admission

        require_business_admission(self)
        return self._require_workload_engine().exec(
            str(workload_id),
            command,
            timeout_s=timeout_s,
            env=env,
        )

    def stop_workload(self, workload_id: str, **kwargs: Any) -> Any:
        """Idempotent stop of a workload (ExecutionPort).

        Not an admission-gated business path: stop/cancel must remain available for
        shutdown and cleanup when business is closed (named residual under
        SD-020 if product misuse appears).
        """
        del kwargs  # reserved for future flags
        return self._require_workload_engine().stop(str(workload_id))

    def workload_status(self, workload_id: str, *, refresh: bool = False) -> Any:
        """Workload snapshot; optional runtime refresh (ExecutionPort)."""
        engine = self._require_workload_engine()
        if refresh:
            return engine.status(str(workload_id), refresh=True)
        return engine.get(str(workload_id))

    def resume_job(self, job_id: str) -> Any:
        """Re-drive a registered orchestration job (ExecutionPort).

        **0.63.25:** product / surface re-drive through this port
        requires admission. Wait plane may still call ``orchestration.resume_job``
        directly — named residual under SD-020 (system continue spine).
        """
        from palm.system.structure.errors import require_business_admission

        self._require_started()
        require_business_admission(self)
        return self.orchestration.resume_job(str(job_id))

    def list_jobs(self, status: Any = None) -> list[Any]:
        """List orchestration jobs (ExecutionPort inspect)."""
        self._require_started()
        return self.orchestration.list_jobs(status=status)

    def list_workloads(
        self,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        session_id: str | None = None,
        status: Any = None,
        runtime: str | None = None,
    ) -> list[Any]:
        """List tracked workloads (ExecutionPort catalog)."""
        return self._require_workload_engine().list(
            job_id=job_id,
            instance_id=instance_id,
            session_id=session_id,
            status=status,
            runtime=runtime,
        )

    def list_workload_runtimes(self) -> list[Any]:
        """Workload runtime catalog with health (ExecutionPort)."""
        return self._require_workload_engine().runtimes()

    def doctor_workloads(self) -> dict[str, Any]:
        """Workload-plane doctor snapshot (ExecutionPort)."""
        return self._require_workload_engine().doctor()

    def stop_owned_workloads(
        self,
        *,
        job_id: str | None = None,
        instance_id: str | None = None,
        session_id: str | None = None,
    ) -> list[Any]:
        """Stop owned workloads (ExecutionPort cancel path)."""
        return self._require_workload_engine().stop_owned(
            job_id=job_id,
            instance_id=instance_id,
            session_id=session_id,
        )

    def _require_workload_engine(self) -> WorkloadEngine:
        engine = self.workload
        if not engine.is_initialized:
            engine.initialize()
        return engine

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError(f"{self.runtime_name} is not started; call start() first")


def _coerce_workload_owner(owner: Any) -> WorkloadOwner | None:
    if owner is None:
        return None
    if isinstance(owner, WorkloadOwner):
        return owner
    if isinstance(owner, dict):
        return WorkloadOwner.from_dict(owner)
    raise TypeError(f"owner must be WorkloadOwner or dict, got {type(owner)!r}")


def _enrich_workload_owner_from_event_context(
    runtime: Any, owner: WorkloadOwner | None
) -> WorkloadOwner:
    """Copy system session / job / instance from active EventContext when missing."""
    base = owner or WorkloadOwner()
    if base.session_id and base.job_id and base.instance_id:
        return base
    event = getattr(runtime, "event", None)
    if event is None or not hasattr(event, "current_context"):
        return base
    try:
        ctx = event.current_context()
    except Exception:
        return base
    if ctx is None:
        return base
    return WorkloadOwner(
        job_id=base.job_id or getattr(ctx, "job_id", None),
        instance_id=base.instance_id or getattr(ctx, "instance_id", None),
        lease_id=base.lease_id,
        session_id=base.session_id or getattr(ctx, "session_id", None),
        created_by_palm=base.created_by_palm,
    )
