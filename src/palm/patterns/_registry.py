"""
Pattern extension registry — builders, instance sync, and submission metadata.

Keeps ``palm.common`` generic; pattern-specific logic lives inside each
``palm.patterns.<name>`` subpackage and registers hooks at import time.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.core.orchestration import Job

if TYPE_CHECKING:
    from palm.common.cqrs.command import Command
    from palm.common.cqrs.projection import Projection
    from palm.common.cqrs.query import Query
    from palm.common.patterns.app import PatternApp
    from palm.common.patterns.build_context import PatternBuildContext
    from palm.core.behavior_tree import BasePattern
    from palm.core.storage import StorageEngine
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
    ReadModelBuilderFn = Callable[..., dict[str, Any]]
    ProjectionFactoryFn = Callable[[StorageEngine], Projection]
    CommandHandlerFn = Callable[[Command, Any], Any]
    QueryHandlerFn = Callable[[Query, Any], Any]
else:
    PatternBuildFn = Callable[..., Any]
    InstanceFieldsFn = Callable[..., Any]
    ResumeStateFn = Callable[..., Any]
    SubmissionMetadataFn = Callable[..., Any]
    ReadModelBuilderFn = Callable[..., dict[str, Any]]
    ProjectionFactoryFn = Callable[..., Any]
    CommandHandlerFn = Callable[..., Any]
    QueryHandlerFn = Callable[..., Any]


@dataclass(frozen=True)
class InteractiveRuntimeHooks:
    """Pattern bridge for instance-keyed input and backtrack operations."""

    is_executable: Callable[[Any], bool]
    previous_step: Callable[[Any, Any], str]


@dataclass(frozen=True)
class ChildWaitHooks:
    """Pattern bridge for nested child-job wait coordination."""

    parent_is_waiting: Callable[[Job], bool]
    poll_child_for_parent: Callable[[Any, str], Any | None]
    resume_parent_after_child: Callable[[Any, Job], Job | None]


@dataclass(frozen=True)
class CqrsContributor:
    """Pattern-owned CQRS command/query types and handler dispatch."""

    pattern_name: str
    command_types: tuple[type, ...] = ()
    query_types: tuple[type, ...] = ()
    handle_command: CommandHandlerFn | None = None
    handle_query: QueryHandlerFn | None = None


McpRegisterFn = Callable[[Any, Any], None]


@dataclass(frozen=True)
class McpContributor:
    """Pattern-owned MCP tools registered on the stdio adapter."""

    pattern_name: str
    register: McpRegisterFn


_lock = threading.RLock()
_builders: dict[str, PatternBuildFn] = {}
_instance_fields: dict[str, InstanceFieldsFn] = {}
_resume_handlers: dict[str, ResumeStateFn] = {}
_submission_metadata: dict[str, SubmissionMetadataFn] = {}
_interactive_runtime: dict[str, InteractiveRuntimeHooks] = {}
_child_wait: dict[str, ChildWaitHooks] = {}
_read_model_builders: dict[str, ReadModelBuilderFn] = {}
_pattern_apps: dict[str, Any] = {}
_projection_factories: dict[str, ProjectionFactoryFn] = {}
_cqrs_contributors: dict[str, CqrsContributor] = {}
_mcp_contributors: dict[str, McpContributor] = {}


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


def register_interactive_runtime(name: str, hooks: InteractiveRuntimeHooks) -> None:
    """Register instance-keyed input/backtrack hooks for interactive pattern ``name``."""
    with _lock:
        if _interactive_runtime.get(name) is hooks:
            return
        _interactive_runtime[name] = hooks


def get_interactive_runtime(name: str) -> InteractiveRuntimeHooks | None:
    """Return interactive runtime hooks for pattern ``name``, if registered."""
    with _lock:
        return _interactive_runtime.get(name)


def register_child_wait(name: str, hooks: ChildWaitHooks) -> None:
    """Register nested child-job wait hooks for pattern ``name``."""
    with _lock:
        if _child_wait.get(name) is hooks:
            return
        _child_wait[name] = hooks


def get_child_wait_hooks(name: str) -> ChildWaitHooks | None:
    """Return child-wait hooks for pattern ``name``, if registered."""
    with _lock:
        return _child_wait.get(name)


def register_read_model_builder(name: str, fn: ReadModelBuilderFn) -> None:
    """Register a pattern-specific REST read-model builder."""
    with _lock:
        if _read_model_builders.get(name) is fn:
            return
        _read_model_builders[name] = fn


def get_read_model_builder(name: str) -> ReadModelBuilderFn | None:
    """Return the read-model builder for pattern ``name``, if registered."""
    with _lock:
        return _read_model_builders.get(name)


def clear_interactive_runtime() -> None:
    """Remove interactive-runtime registrations (primarily for tests)."""
    with _lock:
        _interactive_runtime.clear()


def clear_child_wait() -> None:
    """Remove child-wait registrations (primarily for tests)."""
    with _lock:
        _child_wait.clear()


def clear_read_model_builders() -> None:
    """Remove read-model builder registrations (primarily for tests)."""
    with _lock:
        _read_model_builders.clear()


def register_pattern_app(app: Any) -> None:
    """Register a :class:`~palm.common.patterns.app.PatternApp` instance."""
    with _lock:
        name = str(app.name)
        if _pattern_apps.get(name) is app:
            return
        _pattern_apps[name] = app


def get_pattern_app(name: str) -> Any | None:
    """Return the registered pattern app for ``name``, if any."""
    with _lock:
        return _pattern_apps.get(name)


def installed_pattern_apps() -> list[Any]:
    """Return pattern apps in stable name order."""
    with _lock:
        return [_pattern_apps[name] for name in sorted(_pattern_apps)]


def register_projection_factory(name: str, factory: ProjectionFactoryFn) -> None:
    """Register a pattern-specific CQRS projection factory."""
    with _lock:
        if _projection_factories.get(name) is factory:
            return
        _projection_factories[name] = factory


def get_projection_factory(name: str) -> ProjectionFactoryFn | None:
    """Return the projection factory for pattern ``name``, if registered."""
    with _lock:
        return _projection_factories.get(name)


def registered_projection_factories() -> list[str]:
    """Return sorted pattern names with projection factories."""
    with _lock:
        return sorted(_projection_factories)


def register_cqrs_contributor(contributor: CqrsContributor) -> None:
    """Register pattern-owned CQRS types and handler dispatch."""
    with _lock:
        existing = _cqrs_contributors.get(contributor.pattern_name)
        if existing is contributor:
            return
        _cqrs_contributors[contributor.pattern_name] = contributor


def get_cqrs_contributor(name: str) -> CqrsContributor | None:
    """Return the CQRS contributor for pattern ``name``, if registered."""
    with _lock:
        return _cqrs_contributors.get(name)


def iter_cqrs_contributors() -> list[CqrsContributor]:
    """Return CQRS contributors in stable pattern-name order."""
    with _lock:
        return [_cqrs_contributors[name] for name in sorted(_cqrs_contributors)]


def clear_pattern_apps() -> None:
    """Remove pattern app registrations (primarily for tests)."""
    with _lock:
        _pattern_apps.clear()


def clear_projection_factories() -> None:
    """Remove projection factory registrations (primarily for tests)."""
    with _lock:
        _projection_factories.clear()


def clear_cqrs_contributors() -> None:
    """Remove CQRS contributor registrations (primarily for tests)."""
    with _lock:
        _cqrs_contributors.clear()


def register_mcp_contributor(contributor: McpContributor) -> None:
    """Register pattern-owned MCP tools on the stdio adapter."""
    with _lock:
        existing = _mcp_contributors.get(contributor.pattern_name)
        if existing is contributor:
            return
        _mcp_contributors[contributor.pattern_name] = contributor


def get_mcp_contributor(name: str) -> McpContributor | None:
    """Return the MCP contributor for pattern ``name``, if registered."""
    with _lock:
        return _mcp_contributors.get(name)


def iter_mcp_contributors() -> list[McpContributor]:
    """Return MCP contributors in stable pattern-name order."""
    with _lock:
        return [_mcp_contributors[name] for name in sorted(_mcp_contributors)]


def clear_mcp_contributors() -> None:
    """Remove MCP contributor registrations (primarily for tests)."""
    with _lock:
        _mcp_contributors.clear()
