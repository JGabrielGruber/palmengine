"""
Orchestration engine — job scheduling and lifecycle.

Pure core module: abstract contracts only; concrete modes and backends live outside core.
"""

from palm.core.orchestration.engine import OrchestrationEngine
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.orchestration.exceptions import JobAuthorizationError
from palm.core.orchestration.execution import JobRunner
from palm.core.orchestration.execution_context import ExecutionContext
from palm.core.orchestration.hooks import JobHook, JobHookAdapter
from palm.core.orchestration.input_capable import InputCapable, StepInspectable
from palm.core.orchestration.job import Job, JobStatus
from palm.core.orchestration.job_state import JobState
from palm.core.orchestration.mode import JobScheduler, OrchestrationMode
from palm.core.orchestration.run_result import RunResult

__all__ = [
    "ExecutionContext",
    "InputCapable",
    "Job",
    "JobHook",
    "JobAuthorizationError",
    "JobHookAdapter",
    "JobRunner",
    "JobScheduler",
    "JobState",
    "JobStatus",
    "OrchestrationEngine",
    "OrchestrationEventType",
    "OrchestrationMode",
    "RunResult",
    "StepInspectable",
]
