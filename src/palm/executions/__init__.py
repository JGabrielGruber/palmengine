"""
Executions layer — definition-driven job submission (outside core).

Sits above ``palm.core`` orchestration and below runtimes, translating
``FlowDefinition`` / ``ProcessDefinition`` into executable patterns.
"""

from palm.executions.builder import build_pattern, wizard_config_from_options
from palm.executions.exceptions import (
    DefinitionBuildError,
    DefinitionNotFoundError,
    ExecutionError,
)
from palm.executions.executor import DefinitionExecutor, ProcessExecutor
from palm.executions.repository import DefinitionRepository

__all__ = [
    "DefinitionBuildError",
    "DefinitionExecutor",
    "DefinitionNotFoundError",
    "DefinitionRepository",
    "ExecutionError",
    "ProcessExecutor",
    "build_pattern",
    "wizard_config_from_options",
]