"""
Orchestration engine exceptions.

Pure core module: no imports from outside ``palm.core``.
"""

from __future__ import annotations

from palm.core.exceptions import PalmError


class OrchestrationError(PalmError):
    """Base exception for orchestration failures."""


class JobNotFoundError(OrchestrationError):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job not found: {job_id}")
        self.job_id = job_id


class InvalidJobTransitionError(OrchestrationError):
    def __init__(self, job_id: str, from_status: str, to_status: str) -> None:
        super().__init__(f"Invalid transition for job {job_id}: {from_status} → {to_status}")
        self.job_id = job_id


class JobExecutionError(OrchestrationError):
    def __init__(self, job_id: str, message: str, *, original: BaseException | None = None) -> None:
        super().__init__(f"Job {job_id} execution failed: {message}")
        self.job_id = job_id
        if original is not None:
            self.__cause__ = original


class OrchestratorError(OrchestrationError):
    """Orchestrator-level failures (capacity, duplicate ids, etc.)."""