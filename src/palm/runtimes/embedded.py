"""
Embedded runtime — in-process Palm execution for libraries and tests.

Wires core engines and exposes high-level helpers for orchestrated patterns
(e.g. interactive wizards) without pulling concrete runners into core.
"""

from __future__ import annotations

from typing import Any

import palm.patterns  # — register patterns
import palm.providers  # — register providers
import palm.storages  # noqa: F401 — register backends
from palm import __version__
from palm.backends.behavior_tree import BehaviorTreeRunner
from palm.core import (
    BehaviorTreeEngine,
    ContextEngine,
    EventEngine,
    Job,
    JobScheduler,
    OrchestrationEngine,
    ResourceEngine,
    StorageEngine,
)
from palm.core.context import BaseState
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.executions import DefinitionExecutor, DefinitionRepository, InstanceRepository
from palm.executions.hooks import InstancePersistenceHook
from palm.instances import ProcessInstance
from palm.patterns.wizard import WizardConfig
from palm.runtimes.schedulers import InlineScheduler
from palm.states import BlackboardState


class EmbeddedRuntime:
    """
    In-process runtime coordinating context, events, behavior trees, and jobs.

    This is the primary integration surface for libraries and tests. Call
    :meth:`start` before :meth:`submit_flow`, :meth:`submit_process`, or
    :meth:`resume_process`, and :meth:`stop` when finished.

    Orchestration uses :class:`~palm.runtimes.schedulers.inline.InlineScheduler` with
    :class:`~palm.backends.behavior_tree.BehaviorTreeRunner` by default.
    Pass a shared :class:`~palm.core.storage.StorageEngine` to the constructor
    when instances must survive across multiple runtime lifetimes.
    """

    def __init__(self, *, storage: StorageEngine | None = None) -> None:
        self.context = ContextEngine()
        self.event = EventEngine()
        self.behavior_tree = BehaviorTreeEngine()
        self.resource = ResourceEngine()
        self.orchestration = OrchestrationEngine()
        self._owns_storage = storage is None
        self.storage = storage if storage is not None else StorageEngine()
        self.repository = DefinitionRepository(self.storage)
        self.instances = InstanceRepository(self.storage)
        self.executor = DefinitionExecutor(self, self.repository, self.instances)
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def version(self) -> str:
        return __version__

    def start(self, **options: Any) -> None:
        """Initialize engines, wire orchestration, and begin accepting jobs."""
        if self._started:
            return

        self.context.initialize()
        self.event.initialize()
        self.resource.initialize()

        scheduler = self._resolve_scheduler(options)
        hooks = list(options.get("hooks") or [])
        hooks.append(InstancePersistenceHook(self.instances))

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

        self.storage.initialize(backend=options.get("backend", "memory"))

        self.orchestration.start()
        self._started = True

    def _resolve_scheduler(self, options: dict[str, Any]) -> JobScheduler:
        scheduler = options.get("scheduler") or options.get("mode")
        if scheduler is not None:
            return scheduler

        runner = options.get("runner")
        legacy_backend = options.get("backend")
        if runner is None and legacy_backend is not None and not isinstance(legacy_backend, str):
            runner = legacy_backend
        if runner is None:
            runner = BehaviorTreeRunner()
        return InlineScheduler(runner=runner)

    def stop(self) -> None:
        """Stop orchestration and shut down all engines."""
        if not self._started:
            return

        self.orchestration.stop()
        if self._owns_storage:
            self.storage.shutdown()
        self.orchestration.shutdown()
        self.behavior_tree.shutdown()
        self.resource.shutdown()
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
        """
        Submit a flow definition or repository name/id as an orchestration job.

        Creates a durable :class:`~palm.instances.ProcessInstance` when storage
        is configured. Wizard jobs typically enter ``WAITING_FOR_INPUT`` until
        :meth:`provide_input` is called.
        """
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
        """
        Submit a process definition or repository reference.

        Returns a single ``Job`` when the process has one flow, otherwise a list.
        """
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
        config: WizardConfig | None = None,
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
        """
        Provide input for a waiting interactive job and resume execution.

        Delegates to :meth:`~palm.core.orchestration.engine.OrchestrationEngine.deliver_input`.
        """
        self._require_started()
        return self.orchestration.deliver_input(job_id, value)

    def resume_process(self, instance_id: str) -> Job:
        """
        Resume a persisted process instance.

        Restores wizard answers and step position from storage, registers a new
        job, and returns it ready for :meth:`provide_input` or inspection.
        """
        self._require_started()
        return self.executor.resume_process(instance_id)

    def get_instance(self, instance_id: str) -> ProcessInstance:
        """Load a persisted process instance record."""
        self._require_started()
        return self.instances.get(instance_id)

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

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError("EmbeddedRuntime is not started; call start() first")