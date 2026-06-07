"""
Backward-compatibility package — prefer ``palm.common`` for new code.

Re-exports the shared coordination API formerly rooted here.
"""

from palm.common.exceptions import (
    DefinitionBuildError,
    DefinitionNotFoundError,
    ExecutionError,
    InstanceNotFoundError,
    InstanceResumeError,
    PlanNotFoundError,
    PlanValidationError,
)
from palm.common.executions.executor import DefinitionExecutor
from palm.common.executions.flow_submission import FlowSubmission, prepare_flow_submission
from palm.common.executions.process_submission import prepare_process_plans
from palm.common.hooks.instance_persistence import InstancePersistenceHook
from palm.common.patterns.build_context import PatternBuildContext
from palm.common.patterns.builder import build_pattern, wizard_config_from_options
from palm.common.patterns.wizard_options import parse_wizard_flow_options, wizard_metadata_from_flow
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.common.persistence.instance_repository import InstanceRepository
from palm.common.plans.execution_plan import ExecutionPlan
from palm.common.plans.process_plan import ProcessPlan
from palm.common.plans.registry import PlanRegistry, StoredPlan
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
    "build_pattern",
    "parse_wizard_flow_options",
    "prepare_flow_submission",
    "prepare_process_plans",
    "wizard_config_from_options",
    "wizard_metadata_from_flow",
]