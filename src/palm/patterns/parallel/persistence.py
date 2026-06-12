"""
Parallel instance persistence — branch progress and resume restoration.
"""

from __future__ import annotations

from typing import Any

from palm.core.behavior_tree import PatternStatus
from palm.core.orchestration import Job
from palm.instances import ProcessInstance
from palm.patterns.parallel.keys import ParallelKeys
from palm.patterns.parallel.pattern import ParallelPattern
from palm.states import BlackboardState


def extract_instance_fields_from_job(job: Job) -> tuple[str | None, dict[str, Any]]:
    """Return active branch slug and runtime position for instance persistence."""
    return parallel_step_slug_for_job(job), parallel_runtime_position_for_job(job)


def parallel_step_slug_for_job(job: Job) -> str | None:
    if isinstance(job.executable, ParallelPattern):
        return job.executable.current_step_slug(job.state)
    active = job.state.get(ParallelKeys.ACTIVE_BRANCH)
    return str(active) if active is not None else None


def parallel_runtime_position_for_job(job: Job) -> dict[str, Any]:
    if not isinstance(job.executable, ParallelPattern):
        return {}
    from typing import cast

    return parallel_runtime_position(job.executable, cast(BlackboardState, job.state))


def parallel_runtime_position(pattern: ParallelPattern, state: BlackboardState) -> dict[str, Any]:
    child_results = [
        result.value if result is not None else None for result in pattern.parallel._child_results
    ]
    branches = {
        slug: {
            "completed": runner.completed,
            "scope_entered": runner._scope_entered,
        }
        for slug, runner in pattern.branch_runners().items()
    }
    return {
        "child_results": child_results,
        "branches": branches,
        "merge_complete": bool(state.get(ParallelKeys.MERGE_COMPLETE)),
    }


def prepare_parallel_resume_state(
    instance: ProcessInstance,
    executable: Any,
    state: BlackboardState,
) -> BlackboardState:
    """Restore parallel branch and BT position after loading a snapshot."""
    if not isinstance(executable, ParallelPattern):
        return state

    restore_parallel_position(executable, instance.runtime_position)
    return state


def restore_parallel_position(pattern: ParallelPattern, position: dict[str, Any]) -> None:
    raw_results = position.get("child_results")
    if isinstance(raw_results, list):
        restored: list[PatternStatus | None] = []
        for item in raw_results:
            if item is None:
                restored.append(None)
            else:
                try:
                    restored.append(PatternStatus(str(item)))
                except ValueError:
                    restored.append(None)
        pattern.parallel._child_results = restored

    branches = position.get("branches")
    if isinstance(branches, dict):
        for slug, meta in branches.items():
            runner = pattern.branch_runners().get(str(slug))
            if runner is None or not isinstance(meta, dict):
                continue
            runner.restore_completed(completed=bool(meta.get("completed")))
            runner.restore_scope_entered(entered=bool(meta.get("scope_entered")))
