"""
Pattern extension registry — builders, instance sync, and submission metadata.

Keeps ``palm.common`` generic; pattern-specific logic lives inside each
``palm.patterns.<name>`` subpackage and registers hooks at import time.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.common.patterns.build_context import PatternBuildContext
    from palm.core.behavior_tree import BasePattern
    from palm.core.orchestration import Job
    from palm.definitions.flow import FlowDefinition
    from palm.instances import ProcessInstance
    from palm.states import BlackboardState

    PatternBuildFn = Callable[
        [FlowDefinition, PatternBuildContext, type[BasePattern]],
        BasePattern,
    ]
    InstanceFieldsFn = Callable[[Job], tuple[str | None, dict[str, Any]]]
    ResumeStateFn = Callable[
        [ProcessInstance, Any, BlackboardState],
        BlackboardState,
    ]
    SubmissionMetadataFn = Callable[[FlowDefinition], dict[str, Any]]
else:
    PatternBuildFn = Callable[..., Any]
    InstanceFieldsFn = Callable[..., Any]
    ResumeStateFn = Callable[..., Any]
    SubmissionMetadataFn = Callable[..., Any]

_lock = threading.RLock()
_builders: dict[str, PatternBuildFn] = {}
_instance_fields: dict[str, InstanceFieldsFn] = {}
_resume_handlers: dict[str, ResumeStateFn] = {}
_submission_metadata: dict[str, SubmissionMetadataFn] = {}


def register_builder(name: str, fn: PatternBuildFn) -> None:
    """Register a flow-options builder for pattern ``name``."""
    with _lock:
        if _builders.get(name) is fn:
            return
        _builders[name] = fn


def get_builder(name: str) -> PatternBuildFn | None:
    """Return the registered builder for ``name``, if any."""
    with _lock:
        return _builders.get(name)


def registered_builders() -> list[str]:
    """Return sorted names of patterns with custom builders."""
    with _lock:
        return sorted(_builders)


def clear_builders() -> None:
    """Remove all builder registrations (primarily for tests)."""
    with _lock:
        _builders.clear()


def snapshot_builders() -> dict[str, PatternBuildFn]:
    """Return a shallow copy of registered builders (primarily for tests)."""
    with _lock:
        return dict(_builders)


def restore_builders(saved: dict[str, PatternBuildFn]) -> None:
    """Replace all builder registrations from a prior :func:`snapshot_builders` copy."""
    with _lock:
        _builders.clear()
        _builders.update(saved)


def register_instance_sync(
    name: str,
    *,
    fields: InstanceFieldsFn,
    resume: ResumeStateFn,
) -> None:
    """Register pattern-specific instance field extraction and resume-state hooks."""
    with _lock:
        if _instance_fields.get(name) is fields and _resume_handlers.get(name) is resume:
            return
        _instance_fields[name] = fields
        _resume_handlers[name] = resume


def get_instance_fields(name: str) -> InstanceFieldsFn | None:
    """Return the registered instance-fields extractor for pattern ``name``."""
    with _lock:
        return _instance_fields.get(name)


def get_resume_handler(name: str) -> ResumeStateFn | None:
    """Return the registered resume-state handler for pattern ``name``."""
    with _lock:
        return _resume_handlers.get(name)


def register_submission_metadata(name: str, fn: SubmissionMetadataFn) -> None:
    """Register pattern-specific job metadata enrichment for flow submission."""
    with _lock:
        if _submission_metadata.get(name) is fn:
            return
        _submission_metadata[name] = fn


def get_submission_metadata(name: str) -> SubmissionMetadataFn | None:
    """Return the registered submission metadata enricher for pattern ``name``."""
    with _lock:
        return _submission_metadata.get(name)


def clear_instance_sync() -> None:
    """Remove all instance-sync registrations (primarily for tests)."""
    with _lock:
        _instance_fields.clear()
        _resume_handlers.clear()


def clear_submission_metadata() -> None:
    """Remove all submission-metadata registrations (primarily for tests)."""
    with _lock:
        _submission_metadata.clear()