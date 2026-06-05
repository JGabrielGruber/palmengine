"""
Executions layer — definition-driven job submission (outside core).

Sits above ``palm.core`` orchestration and below runtimes, translating
``FlowDefinition`` / ``ProcessDefinition`` into executable patterns.
"""

from palm.executions.builder import build_pattern, wizard_config_from_options
from palm.executions.exceptions import DefinitionBuildError, ExecutionError
from palm.executions.executor import DefinitionExecutor, ProcessExecutor

__all__ = [
    "DefinitionBuildError",
    "DefinitionExecutor",
    "ExecutionError",
    "ProcessExecutor",
    "build_pattern",
    "wizard_config_from_options",
]