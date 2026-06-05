"""
BehaviorTreeBackend — concrete ExecutionBackend for running Palm Behavior Trees as Jobs.

Location note:
    This file lives in `palm/backends/` (outside `palm.core`) deliberately.
    The core Orchestration Engine (`palm/core/orchestration`) must have **zero**
    dependencies on the Behavior Tree Engine. All BT-specific execution logic
    belongs here.

This backend allows an `Orchestrator` (or `TestMode` / future modes) to treat
a `BehaviorTree` instance as a first-class `Job.executable`.

It is intended for composition use cases (e.g. interactive wizards rebuilt on
top of the clean core). Most unit tests for the Orchestration Engine itself
continue to use the pure `TestBackend` from the core package.

Usage (outside core):
    from palm.backends.behavior_tree import BehaviorTreeBackend
    from palm.core.orchestration import Orchestrator, TestMode

    backend = BehaviorTreeBackend()
    mode = TestMode(backend=backend)   # or a real EmbeddedMode later
    orch = Orchestrator(mode=mode)
    job = orch.submit(my_behavior_tree)
"""

from __future__ import annotations

from palm.core.behavior_tree import BehaviorTree, NodeStatus
from palm.core.orchestration.exceptions import JobExecutionError
from palm.core.orchestration.execution.backend import ExecutionBackend
from palm.core.orchestration.job import Job, JobStatus


class BehaviorTreeBackend(ExecutionBackend):
    """
    ExecutionBackend implementation that knows how to advance a `BehaviorTree`
    submitted as a Job's executable.

    This is *not* part of the pure `palm.core.orchestration` package. It is a
    reusable composition adapter placed in the `palm/backends/` namespace.
    """

    def advance(self, job: Job, *, max_steps: int | None = 10_000) -> JobStatus:
        if not isinstance(job.executable, BehaviorTree):
            raise JobExecutionError(
                job.id,
                "BehaviorTreeBackend can only execute BehaviorTree instances",
            )

        tree: BehaviorTree = job.executable
        job._allow_mutation = True

        try:
            if job.status == JobStatus.PENDING:
                job._transition_to(JobStatus.RUNNING)

            if max_steps is None:
                max_steps = 10_000

            try:
                final = tree.tick_until_terminal(max_ticks=max_steps)
            except Exception as exc:  # BehaviorTreeError or others
                job._transition_to(JobStatus.FAILED, error=exc)
                raise JobExecutionError(job.id, "BehaviorTree tick failed", original=exc) from exc

            # Map NodeStatus → JobStatus (using conventional blackboard keys for results)
            if final == NodeStatus.SUCCESS:
                result = tree.blackboard.get("__result__")
                job._transition_to(JobStatus.SUCCEEDED, result=result)
            elif final == NodeStatus.FAILURE:
                err = tree.blackboard.get("__error__")
                job._transition_to(JobStatus.FAILED, error=err)
            elif final == NodeStatus.WAITING_FOR_INPUT:
                job._transition_to(JobStatus.WAITING_FOR_INPUT)
            else:
                # RUNNING exhausted the tick budget — treat as failure for safety
                job._transition_to(JobStatus.FAILED, error=RuntimeError("Behavior tree did not terminate"))

            return job.status

        finally:
            job._allow_mutation = False
