"""
Shared coordination logic for Palm (non-plugin, non-core).

``palm.common`` holds definition-driven submission, plan staging, persistence
helpers, orchestration hooks, and pattern materialization — the glue between
``palm.core`` engines, ``palm.definitions``, and extensible ``palm.patterns``.

Extensible plugins live elsewhere:

- ``palm.patterns`` — register via ``pattern_registry``
- ``palm.providers`` — register via ``provider_registry``
- ``palm.storages`` — register via ``storage_registry``
- ``palm.common.transforms`` — built-in rules + ``transform_registry`` helpers
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.common.executions.executor import DefinitionExecutor
    from palm.common.executions.flow_submission import FlowSubmission
    from palm.common.hooks.instance_persistence import InstancePersistenceHook
    from palm.common.patterns.build_context import PatternBuildContext
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.common.persistence.instance_repository import InstanceRepository
    from palm.common.plans.execution_plan import ExecutionPlan
    from palm.common.plans.process_plan import ProcessPlan
    from palm.common.plans.registry import PlanRegistry, StoredPlan
    from palm.common.transforms.execution import TransformExecutor
    from palm.common.transforms.registration import register_transform, transform_rule
    from palm.instances import ProcessInstance, StatusHistoryEntry

__all__ = [
    "DefinitionBuildError",
    "DefinitionExecutor",
    "DefinitionNotFoundError",
    "DefinitionRepository",
    "ExecutionError",
    "ExecutionPlan",
    "FlowSubmission",
    "InstanceNotFoundError",
    "InstancePersistenceHook",
    "InstanceRepository",
    "InstanceResumeError",
    "PatternBuildContext",
    "PlanNotFoundError",
    "PlanRegistry",
    "PlanValidationError",
    "ProcessInstance",
    "ProcessPlan",
    "StatusHistoryEntry",
    "StoredPlan",
    "TransformExecutor",
    "build_pattern",
    "register_transform",
    "transform_rule",
    "prepare_flow_submission",
    "prepare_process_plans",
]

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "DefinitionBuildError": ("palm.common.exceptions", "DefinitionBuildError"),
    "DefinitionNotFoundError": ("palm.common.exceptions", "DefinitionNotFoundError"),
    "ExecutionError": ("palm.common.exceptions", "ExecutionError"),
    "InstanceNotFoundError": ("palm.common.exceptions", "InstanceNotFoundError"),
    "InstanceResumeError": ("palm.common.exceptions", "InstanceResumeError"),
    "PlanNotFoundError": ("palm.common.exceptions", "PlanNotFoundError"),
    "PlanValidationError": ("palm.common.exceptions", "PlanValidationError"),
    "DefinitionExecutor": ("palm.common.executions.executor", "DefinitionExecutor"),
    "FlowSubmission": ("palm.common.executions.flow_submission", "FlowSubmission"),
    "prepare_flow_submission": (
        "palm.common.executions.flow_submission",
        "prepare_flow_submission",
    ),
    "prepare_process_plans": ("palm.common.executions.process_submission", "prepare_process_plans"),
    "InstancePersistenceHook": (
        "palm.common.hooks.instance_persistence",
        "InstancePersistenceHook",
    ),
    "PatternBuildContext": ("palm.common.patterns.build_context", "PatternBuildContext"),
    "build_pattern": ("palm.common.patterns.builder", "build_pattern"),
    "DefinitionRepository": (
        "palm.common.persistence.definition_repository",
        "DefinitionRepository",
    ),
    "InstanceRepository": ("palm.common.persistence.instance_repository", "InstanceRepository"),
    "ExecutionPlan": ("palm.common.plans.execution_plan", "ExecutionPlan"),
    "ProcessPlan": ("palm.common.plans.process_plan", "ProcessPlan"),
    "PlanRegistry": ("palm.common.plans.registry", "PlanRegistry"),
    "StoredPlan": ("palm.common.plans.registry", "StoredPlan"),
    "TransformExecutor": ("palm.common.transforms.execution", "TransformExecutor"),
    "register_transform": ("palm.common.transforms.registration", "register_transform"),
    "transform_rule": ("palm.common.transforms.registration", "transform_rule"),
    "ProcessInstance": ("palm.instances", "ProcessInstance"),
    "StatusHistoryEntry": ("palm.instances", "StatusHistoryEntry"),
}


def __getattr__(name: str) -> object:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_path, attr = _LAZY_EXPORTS[name]
    import importlib

    module = importlib.import_module(module_path)
    value = getattr(module, attr)
    globals()[name] = value
    return value
