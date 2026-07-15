"""
Wizard bridge hooks — register pattern-specific runtime surfaces on ``_registry``.

Keeps ``palm.common`` free of direct wizard imports; common dispatches through
:mod:`palm.common.patterns._registry` instead.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.common.patterns._registry import (
    ChildWaitHooks,
    InteractiveRuntimeHooks,
    register_child_wait,
    register_interactive_runtime,
    register_read_model_builder,
)
from palm.patterns.wizard.bindings.behavior_tree.backtrack import can_backtrack_to
from palm.patterns.wizard.bindings.resource.child_wait import (
    child_job_id_from_wait,
    get_child_wait,
    poll_child_job,
)
from palm.patterns.wizard.pattern import WizardPattern


def _is_wizard_executable(executable: Any) -> bool:
    return isinstance(executable, WizardPattern)


def _wizard_previous_step(executable: Any, state: Any) -> str:
    wizard = executable
    current = wizard.current_step_slug(state)
    if current is None:
        raise ValueError("Wizard has no active step; cannot backtrack")

    config = wizard.config
    if not config.allow_backtrack:
        raise ValueError("Backtracking is disabled for this wizard")

    index = config.index_of(current)
    if index <= 0:
        raise ValueError("Already at the first step; cannot backtrack further")

    steps = config.iter_tree_steps()
    target = steps[index - 1].slug
    if not can_backtrack_to(config, target):
        raise ValueError(f"Cannot backtrack to step: {target!r}")
    return target


def _wizard_parent_is_waiting(job: Job) -> bool:
    waiting = get_child_wait(job.state)
    return isinstance(waiting, dict) and bool(waiting.get("child_job_id"))


def _wizard_poll_child_for_parent(_state: Any, child_job_id: str) -> Job | None:
    from palm.common.providers._registry import get_bound_runtime

    runtime = get_bound_runtime()
    if runtime is None:
        return None
    return poll_child_job(runtime, child_job_id)


def _wizard_resume_parent_after_child(runtime: Any, child_job: Job) -> Job | None:
    if child_job.status != JobStatus.SUCCEEDED:
        return None
    parent_id = child_job.metadata.get("__palm:parent_job_id")
    if not parent_id:
        return None
    try:
        parent = runtime.get_job(str(parent_id))
    except JobNotFoundError:
        return None
    if parent.status != JobStatus.WAITING_FOR_INPUT:
        return None
    waiting = get_child_wait(parent.state)
    child_id = child_job_id_from_wait(waiting)
    if child_id and child_id != child_job.id:
        return None
    runtime.orchestration.resume_job(parent.id)
    return runtime.get_job(parent.id)


def register_wizard_bridges() -> None:
    """Wire wizard runtime bridges into the global pattern extension registry."""
    register_interactive_runtime(
        "wizard",
        InteractiveRuntimeHooks(
            is_executable=_is_wizard_executable,
            previous_step=_wizard_previous_step,
        ),
    )
    register_child_wait(
        "wizard",
        ChildWaitHooks(
            parent_is_waiting=_wizard_parent_is_waiting,
            poll_child_for_parent=_wizard_poll_child_for_parent,
            resume_parent_after_child=_wizard_resume_parent_after_child,
        ),
    )
    from palm.patterns.wizard.bindings.read_model import build_wizard_view

    register_read_model_builder("wizard", build_wizard_view)
