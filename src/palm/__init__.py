"""
Palm Orchestration Engine (🌴)

A lightweight but powerful orchestration engine for running multi-step transactional
workflows that feature rich interactive wizards.

Wizards are stateful, concurrent, hierarchical DAGs that behave like lightweight
Behavior Trees. They support user interaction, validation, backtracking,
rich context, and transactional commit steps.

Key principles:
- Core is pure logic (no UI)
- Sessions are persistent with TTL
- Wizards only advance on explicit user "ticks" (input)
- First step is always a non-backtrackable Introduction
"""

__version__ = "0.2.2"

from palm.exceptions import (
    BacktrackNotAllowedError,
    InvalidStepError,
    PalmError,
    SessionExpiredError,
    SessionNotFoundError,
    ValidationError,
    WizardNotFoundError,
)

__all__ = [
    "__version__",
    "PalmError",
    "WizardNotFoundError",
    "SessionNotFoundError",
    "InvalidStepError",
    "ValidationError",
    "BacktrackNotAllowedError",
    "SessionExpiredError",
]
