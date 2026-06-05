"""
Embedded runtime — in-process Palm execution for libraries and tests.

Wires core engines and exposes high-level helpers for orchestrated patterns
(e.g. interactive wizards) without pulling execution backends into core.
"""

from __future__ import annotations

from typing import Any

import palm.patterns  # — register patterns
import palm.providers  # — register providers
import palm.storages  # noqa: F401 — register backends
from palm import __version__
from palm.backends.behavior_tree import BehaviorTreeBackend
from palm.core import (
    BehaviorTreeEngine,
    ContextEngine,
    EventEngine,
    Job,
    OrchestrationEngine,
    StorageEngine,
    TestMode,
)
from palm.core.context import BaseState
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.executions import DefinitionExecutor
from palm.patterns.wizard import WizardConfig, WizardPattern
from palm.states import BlackboardState


class EmbeddedRuntime:
    """
    In-process runtime coordinating context, events, behavior trees, and jobs.

    Orchestration uses ``TestMode`` with ``BehaviorTreeBackend`` by default so
    pattern executables (e.g. ``WizardPattern``) advance through the job API.
    """

    def __init__(self) -> None:
        self.context = ContextEngine()
        self.event = EventEngine()
        self.behavior_tree = BehaviorTreeEngine()
        self.orchestration = OrchestrationEngine()
        self.storage = StorageEngine()
        self.executor = DefinitionExecutor(self)
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

        mode = options.get("mode")
        if mode is None:
            mode = TestMode(backend=BehaviorTreeBackend())

        orch_options: dict[str, Any] = {
            "mode": mode,
            "event_engine": self.event,
            "context_engine": self.context,
        }
        max_jobs = options.get("max_concurrent_jobs")
        if isinstance(max_jobs, int) and max_jobs > 0:
            orch_options["max_concurrent_jobs"] = max_jobs
        self.orchestration.initialize(**orch_options)

        state = options.get("state")
        bt_state: BaseState = (
            state if isinstance(state, BaseState) else BlackboardState()
        )
        self.behavior_tree.initialize(state=bt_state)

        self.storage.initialize(backend=options.get("backend", "memory"))

        self.orchestration.start()
        self._started = True

    def stop(self) -> None:
        """Stop orchestration and shut down all engines."""
        if not self._started:
            return

        self.orchestration.stop()
        self.storage.shutdown()
        self.orchestration.shutdown()
        self.behavior_tree.shutdown()
        self.context.shutdown()
        self.event.shutdown()
        self._started = False

    def submit_flow(
        self,
        flow: FlowDefinition,
        *,
        job_id: str | None = None,
        state: BlackboardState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Submit a flow definition as an orchestration job."""
        return self.executor.submit_flow(
            flow,
            job_id=job_id,
            state=state,
            metadata=metadata,
        )

    def submit_process(
        self,
        process: ProcessDefinition,
        *,
        job_id: str | None = None,
        state: BlackboardState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job | list[Job]:
        """
        Submit all flows on a process definition.

        Returns a single ``Job`` when the process has one flow, otherwise a list.
        """
        jobs = self.executor.submit_process(
            process,
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
        Provide input for a waiting wizard job and resume execution.

        Returns the step slug that received the input, or ``None`` if the job
        is not a wizard or no step is waiting.
        """
        self._require_started()
        wizard = self._wizard_for_job(job_id)
        job = self.orchestration.get_job(job_id)
        slug = wizard.provide_input(job.state, value)
        self.orchestration.resume_job(job_id)
        return slug

    def get_job(self, job_id: str) -> Job:
        """Return a registered orchestration job."""
        self._require_started()
        return self.orchestration.get_job(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a non-terminal job."""
        self._require_started()
        return self.orchestration.cancel_job(job_id)

    def current_wizard_step(self, job_id: str) -> str | None:
        """Return the active wizard step slug for a job, if applicable."""
        self._require_started()
        wizard = self._wizard_for_job(job_id)
        return wizard.current_step_slug(self.orchestration.get_job(job_id).state)

    def wizard_answers(self, job_id: str) -> dict[str, Any]:
        """Return collected wizard answers for a job."""
        self._require_started()
        wizard = self._wizard_for_job(job_id)
        return wizard.answers(self.orchestration.get_job(job_id).state)

    def _wizard_for_job(self, job_id: str) -> WizardPattern:
        try:
            job = self.orchestration.get_job(job_id)
        except JobNotFoundError:
            raise
        executable = job.executable
        if not isinstance(executable, WizardPattern):
            raise TypeError(f"Job {job_id!r} is not a wizard job")
        return executable

    def _require_started(self) -> None:
        if not self._started:
            raise RuntimeError("EmbeddedRuntime is not started; call start() first")