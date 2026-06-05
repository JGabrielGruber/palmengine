"""
Orchestration Engine specific exceptions.

All exceptions inherit from PalmError (top-level) so callers can catch the
broad `palm.exceptions.PalmError` while still allowing fine-grained handling
of job lifecycle vs. execution vs. mode errors.

This module is part of Palm's general-purpose Orchestration Engine and must
remain completely independent of any wizard, UI, persistence, or domain concerns.
"""

from __future__ import annotations

from palm.exceptions import PalmError


class OrchestrationError(PalmError):
    """
    Base exception for all errors originating inside the Orchestration Engine.

    This is the class users of the engine should primarily catch when they want
    to handle "something went wrong while managing or executing jobs".
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message, code=code or "ORCHESTRATION_ERROR")


class JobNotFoundError(OrchestrationError):
    """Raised when an operation references a job_id that does not exist."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job not found: {job_id}", code="JOB_NOT_FOUND")
        self.job_id = job_id


class InvalidJobTransitionError(OrchestrationError):
    """
    Raised when a Job is asked to move to an illegal status
    (e.g. SUCCEEDED → RUNNING, or CANCELLED → anything).
    """

    def __init__(self, job_id: str, from_status: str, to_status: str) -> None:
        msg = f"Invalid transition for job {job_id}: {from_status} → {to_status}"
        super().__init__(msg, code="INVALID_JOB_TRANSITION")
        self.job_id = job_id
        self.from_status = from_status
        self.to_status = to_status


class JobExecutionError(OrchestrationError):
    """
    Wraps an unexpected failure that occurred while a backend was advancing a job.

    The original exception (if any) is preserved as `__cause__`.
    """

    def __init__(self, job_id: str, message: str, *, original: BaseException | None = None) -> None:
        super().__init__(f"Job {job_id} execution failed: {message}", code="JOB_EXECUTION_ERROR")
        self.job_id = job_id
        if original is not None:
            self.__cause__ = original


class OrchestratorError(OrchestrationError):
    """General orchestrator-level failures (max jobs exceeded, shutdown races, etc.)."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message, code=code or "ORCHESTRATOR_ERROR")


class ModeError(OrchestrationError):
    """Errors raised by a specific OrchestrationMode implementation."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message, code=code or "MODE_ERROR")
