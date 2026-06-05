"""
Executions layer — definition-driven job submission (outside core).

Sits above ``palm.core`` orchestration and below runtimes, translating
``FlowDefinition`` / ``ProcessDefinition`` into executable patterns.
"""

from palm.executions.build_context import PatternBuildContext
from palm.executions.builder import build_pattern, wizard_config_from_options
from palm.executions.exceptions import (
    DefinitionBuildError,
    DefinitionNotFoundError,
    ExecutionError,
    InstanceNotFoundError,
    InstanceResumeError,
)
from palm.executions.executor import DefinitionExecutor, ProcessExecutor
from palm.executions.instance_repository import InstanceRepository
from palm.executions.repository import DefinitionRepository
from palm.executions.wizard_options import parse_wizard_flow_options, wizard_metadata_from_flow
from palm.instances import ProcessInstance, StatusHistoryEntry

__all__ = [
    "DefinitionBuildError",
    "DefinitionExecutor",
    "DefinitionNotFoundError",
    "DefinitionRepository",
    "ExecutionError",
    "InstanceNotFoundError",
    "InstanceRepository",
    "InstanceResumeError",
    "PatternBuildContext",
    "ProcessExecutor",
    "ProcessInstance",
    "StatusHistoryEntry",
    "build_pattern",
    "parse_wizard_flow_options",
    "wizard_config_from_options",
    "wizard_metadata_from_flow",
]
