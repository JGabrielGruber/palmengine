"""
PalmApp — infrastructure layer for Palm Engine (storage, runtimes, definitions).

Prefer :class:`~palm.app.host.ApplicationHost` for orchestration with CQRS and recovery.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from palm.app.bootstrap import (
    ensure_plugins,
    load_definitions_for_repository,
    runtime_start_options,
)
from palm.app.registry import RuntimeHandle, RuntimeKind, RuntimeRegistry
from palm.app.settings import PalmSettings
from palm.common.managers import InstanceManager, InstanceSummary
from palm.common.persistence.instance_repository import InstanceRepository
from palm.core.storage import StorageEngine

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.common.runtimes.base import BaseRuntime
    from palm.core.orchestration import Job
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition
    from palm.definitions.resource import ResourceDefinition
    from palm.instances import ProcessInstance, StateSnapshot

class PalmApp:
    """
    Infrastructure layer — shared storage, instance manager, and runtime registry.

    For role-based orchestration, CQRS, and recovery, prefer
    :class:`~palm.app.host.ApplicationHost`, which wraps ``PalmApp`` as its
    infrastructure delegate.

    A single ``PalmApp`` can host multiple runtimes (embedded, daemon, server)
    that share one :class:`~palm.core.storage.StorageEngine` for durable
    definitions and instances.

    Typical usage::

        app = PalmApp().bootstrap()
        embedded = app.create_runtime("embedded", autostart=True)
        daemon = app.create_runtime("daemon", name="worker", autostart=True)
        app.load_definitions()
    """

    def __init__(
        self,
        settings: PalmSettings | None = None,
        *,
        storage: StorageEngine | None = None,
    ) -> None:
        self.settings = settings or PalmSettings()
        self._owns_storage = storage is None
        self.storage = storage if storage is not None else StorageEngine()
        self._instance_repository = InstanceRepository(self.storage)
        self._instance_manager = InstanceManager(
            self._instance_repository,
            settings=self.settings,
        )
        self._runtimes = RuntimeRegistry()
        self._primary: str | None = None
        self._bootstrapped = False

    @property
    def is_bootstrapped(self) -> bool:
        return self._bootstrapped

    @property
    def primary_name(self) -> str | None:
        return self._primary

    @property
    def instance_manager(self) -> InstanceManager:
        """Shared instance lifecycle coordinator across runtimes."""
        return self._instance_manager

    def bootstrap(self) -> Self:
        """Load plugin apps and mark the application ready for runtime creation."""
        ensure_plugins()
        self._bootstrapped = True
        return self

    def create_runtime(
        self,
        kind: RuntimeKind,
        *,
        name: str | None = None,
        autostart: bool = False,
        set_primary: bool | None = None,
        **start_options: Any,
    ) -> BaseRuntime:
        """
        Construct and optionally start a named runtime sharing app storage.

        Parameters
        ----------
        kind:
            ``embedded``, ``daemon``, or ``server``.
        name:
            Registry key. Defaults to ``kind`` or ``{kind}-{n}`` when taken.
        autostart:
            When ``True``, call :meth:`start` before returning.
        set_primary:
            When ``True``, make this runtime the default for :attr:`runtime`.
            Defaults to ``True`` when this is the first registered runtime.
        """
        self._require_bootstrapped()
        runtime_name = name or self._default_runtime_name(kind)
        runtime = self._build_runtime(kind, **start_options)
        handle = RuntimeHandle(name=runtime_name, kind=kind, runtime=runtime)
        self._runtimes.register(handle)

        if set_primary is True or (set_primary is None and self._primary is None):
            self._primary = runtime_name

        if autostart:
            self.start(runtime_name, **start_options)
        return runtime

    def runtime(self, name: str | None = None) -> BaseRuntime:
        """Return a registered runtime (primary by default)."""
        handle = self._runtimes.get(name or self._require_primary_name())
        return handle.runtime

    def repository(self, *, runtime_name: str | None = None) -> DefinitionRepository:
        """Return the definition repository for a registered runtime."""
        return self.runtime(runtime_name).repository

    def resolve_flow(self, ref: str, *, runtime_name: str | None = None) -> FlowDefinition:
        """Resolve a flow by display name, falling back to definition id."""
        from palm.app.resolvers import resolve_flow_for_app

        return resolve_flow_for_app(self, ref, runtime_name=runtime_name)

    def resolve_process(self, ref: str, *, runtime_name: str | None = None) -> ProcessDefinition:
        """Resolve a process by display name, falling back to definition id."""
        from palm.app.resolvers import resolve_process_for_app

        return resolve_process_for_app(self, ref, runtime_name=runtime_name)

    def resolve_resource(self, ref: str, *, runtime_name: str | None = None) -> ResourceDefinition:
        """Resolve a resource by display name, falling back to definition id."""
        from palm.app.resolvers import resolve_resource_for_app

        return resolve_resource_for_app(self, ref, runtime_name=runtime_name)

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
        """Submit a flow on a registered runtime (primary by default)."""
        return self.runtime(runtime_name).submit_flow(
            ref,
            by_id=by_id,
            job_id=job_id,
            state=state,
            metadata=metadata,
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
        """Submit a process on a registered runtime (primary by default)."""
        return self.runtime(runtime_name).submit_process(
            ref,
            by_id=by_id,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def resume_process(self, instance_id: str, *, runtime_name: str | None = None) -> Job:
        """Resume a persisted process instance on a registered runtime."""
        return self.runtime(runtime_name).resume_process(instance_id)

    def provide_input(
        self, job_id: str, value: Any, *, runtime_name: str | None = None
    ) -> str | None:
        """Deliver interactive input and resume the job on a registered runtime."""
        return self.runtime(runtime_name).provide_input(job_id, value)

    def get_job(self, job_id: str, *, runtime_name: str | None = None) -> Job:
        """Return an orchestration job from a registered runtime."""
        return self.runtime(runtime_name).get_job(job_id)

    def get_instance(self, instance_id: str, *, runtime_name: str | None = None) -> ProcessInstance:
        """Load a persisted process instance from the shared manager."""
        _ = runtime_name
        return self._instance_manager.get(instance_id)

    def list_instances(self, *, runtime_name: str | None = None) -> list[ProcessInstance]:
        """List durable process instances (full load via manager)."""
        _ = runtime_name
        return self._instance_manager.list_instances()

    def list_instance_summaries(self, *, runtime_name: str | None = None) -> list[InstanceSummary]:
        """List lightweight instance summaries without loading full payloads."""
        _ = runtime_name
        return self._instance_manager.list_summaries()

    def list_instance_snapshots(
        self, instance_id: str, *, runtime_name: str | None = None
    ) -> list[StateSnapshot]:
        """Return point-in-time state snapshots for a persisted instance."""
        _ = runtime_name
        return self._instance_manager.list_state_snapshots(instance_id)

    def list_flows(self, *, runtime_name: str | None = None) -> list[FlowDefinition]:
        """List flow definitions from a registered runtime repository."""
        return self.repository(runtime_name=runtime_name).list_flows()

    def list_processes(self, *, runtime_name: str | None = None) -> list[ProcessDefinition]:
        """List process definitions from a registered runtime repository."""
        return self.repository(runtime_name=runtime_name).list_processes()

    def list_resources(self, *, runtime_name: str | None = None) -> list[ResourceDefinition]:
        """List resource definitions from a registered runtime repository."""
        return self.repository(runtime_name=runtime_name).list_resources()

    def current_wizard_step(self, job_id: str, *, runtime_name: str | None = None) -> str | None:
        """Return the active wizard step slug when applicable."""
        return self.runtime(runtime_name).current_wizard_step(job_id)

    def resume_job(self, job_id: str, *, runtime_name: str | None = None) -> None:
        """Resume orchestration for a registered job."""
        self.runtime(runtime_name).orchestration.resume_job(job_id)

    def persist_job(self, job: Job, *, runtime_name: str | None = None) -> None:
        """Persist job state through a registered runtime executor."""
        self.runtime(runtime_name).executor.persist_job(job)

    def is_runtime_started(self, name: str | None = None) -> bool:
        """Return whether a registered runtime has been started."""
        return self.runtime(name).is_started

    def get_handle(self, name: str) -> RuntimeHandle:
        """Return the registry record for a named runtime."""
        return self._runtimes.get(name)

    def set_primary(self, name: str) -> None:
        """Choose the default runtime returned by :attr:`runtime`."""
        self._runtimes.get(name)  # validate
        self._primary = name

    def start(self, name: str, **options: Any) -> BaseRuntime:
        """Start a registered runtime using app settings merged with ``options``."""
        handle = self._runtimes.get(name)
        if handle.runtime.is_started:
            return handle.runtime
        merged = runtime_start_options(self.settings, **options)
        handle.runtime.start(**merged)
        return handle.runtime

    def stop(self, name: str) -> None:
        """Stop a single runtime without shutting down shared storage."""
        self._runtimes.get(name).runtime.stop()

    def load_definitions(self, *, name: str | None = None) -> int:
        """
        Hydrate definition catalogs for one or all registered runtimes.

        Returns the total number of definition records touched.
        """
        if name is not None:
            handle = self._runtimes.get(name)
            return load_definitions_for_repository(handle.runtime.repository, self.settings)

        total = 0
        for handle in self._runtimes.items():
            total += load_definitions_for_repository(handle.runtime.repository, self.settings)
        return total

    def running(self) -> list[str]:
        """Return names of runtimes that are currently started."""
        return [handle.name for handle in self._runtimes.items() if handle.is_started]

    def shutdown(self) -> None:
        """Stop all runtimes and release shared storage when owned by the app."""
        for handle in self._runtimes.items():
            if handle.is_started:
                handle.runtime.stop()
        self._instance_manager.shutdown()
        if self._owns_storage and self.storage.is_initialized:
            self.storage.shutdown()
        self._runtimes.clear()
        self._primary = None

    def __enter__(self) -> Self:
        if not self._bootstrapped:
            self.bootstrap()
        return self

    def __exit__(self, *exc: object) -> None:
        self.shutdown()

    def _build_runtime(self, kind: RuntimeKind, **options: Any) -> BaseRuntime:
        if kind == "embedded":
            from palm.runtimes.embedded import EmbeddedRuntime

            return EmbeddedRuntime(
                storage=self.storage,
                instance_manager=self._instance_manager,
            )
        if kind == "daemon":
            from palm.runtimes.daemon import DaemonRuntime

            return DaemonRuntime(
                storage=self.storage,
                instance_manager=self._instance_manager,
            )
        if kind == "server":
            from palm.runtimes.server import ServerRuntime

            return ServerRuntime(
                storage=self.storage,
                instance_manager=self._instance_manager,
                host=str(options.pop("host", "127.0.0.1")),
                port=int(options.pop("port", 8080)),
            )
        raise ValueError(f"Unknown runtime kind {kind!r}")

    def _default_runtime_name(self, kind: RuntimeKind) -> str:
        if kind not in self._runtimes.names():
            return kind
        index = 1
        while f"{kind}-{index}" in self._runtimes:
            index += 1
        return f"{kind}-{index}"

    def _require_primary_name(self) -> str:
        if self._primary is None:
            raise RuntimeError("No primary runtime; call create_runtime() first")
        return self._primary

    def _require_bootstrapped(self) -> None:
        if not self._bootstrapped:
            raise RuntimeError("PalmApp is not bootstrapped; call bootstrap() first")
