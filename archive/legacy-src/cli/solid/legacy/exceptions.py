"""
DEPRECATION NOTICE
------------------
This file contains the wizard-/orchestrator-specific exceptions that were
previously defined in palm/exceptions.py.

Moved as part of the 0.3.0-dev clean-core migration into the legacy reference
implementation. These exceptions are preserved only for backward compatibility
with the old code paths.

New code should import only the base `PalmError` from `palm.exceptions` and
should not depend on these specific legacy errors.

Last updated: 0.3.0-dev migration
"""

from __future__ import annotations

from palm.exceptions import PalmError


class WizardNotFoundError(PalmError):
    """Requested wizard definition was not found in the registry."""


class SessionNotFoundError(PalmError):
    """Session ID does not exist or has been purged."""


class SessionExpiredError(PalmError):
    """Session TTL has elapsed and the session is no longer usable."""


class InvalidStepError(PalmError):
    """Step slug is invalid for the current wizard or state."""


class ValidationError(PalmError):
    """User input failed validation rules for the current step."""

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        errors: list[str] | None = None,
    ) -> None:
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field
        self.errors = errors or [message]


class BacktrackNotAllowedError(PalmError):
    """Attempted to backtrack to a step that is not permitted (e.g. introduction)."""


class CommitError(PalmError):
    """Transactional commit step failed."""


class ProcessManagerError(PalmError):
    """Error in the ProcessManager (spawning, communication, termination)."""


__all__ = [
    "PalmError",
    "WizardNotFoundError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "InvalidStepError",
    "ValidationError",
    "BacktrackNotAllowedError",
    "CommitError",
    "ProcessManagerError",
]
