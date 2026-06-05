"""
Palm Legacy Reference Implementation (0.3.0-dev)

This package contains the complete pre-Behavior-Tree-era Palm code
(wizard engine, models, persistence, orchestrator, events, workflow, etc.).

It is provided **only** for historical reference and to keep the existing
Solid CLI working without modification during the 0.3.0 structural cleanup phase.

DEPRECATION NOTICE
------------------
This entire package (`palm.cli.solid.legacy.*`) is deprecated.
It has been relocated from the clean core as part of the v0.3.0 migration.

New code MUST NOT depend on anything under this package.
Future domain features (including the real wizard implementation) will be
built on top of `palm.core.behavior_tree` in a clean, new location.

See ARCHITECTURE.md and AGENTS.md for the current rules.

Last updated: 0.3.0-dev migration
"""

from __future__ import annotations

# Re-exports for (slightly) more convenient access during the transition period.
# These are legacy symbols only.
from .events import Event, EventBus

# Legacy-specific exceptions (base PalmError now lives in palm.exceptions)
from .exceptions import (
    BacktrackNotAllowedError,
    CommitError,
    InvalidStepError,
    PalmError,
    ProcessManagerError,
    SessionExpiredError,
    SessionNotFoundError,
    ValidationError,
    WizardNotFoundError,
)
from .models.common import SessionStatus, StepType, ValidationRule
from .models.session import WizardSession
from .models.step import StepDefinition
from .orchestrator import Orchestrator
from .persistence.sqlite import SQLiteSessionStore
from .process_manager import ProcessManager
from .utils.graph import find_path, topological_sort

# Internal legacy helpers (re-exported for compatibility)
from .utils.time import add_seconds, is_expired, utc_now
from .wizard.context import RichContext
from .wizard.definition import WizardDefinition
from .wizard.engine import WizardEngine
from .wizard.session import WizardSessionState as WizardSession

__all__ = [
    "Event",
    "EventBus",
    "Orchestrator",
    "ProcessManager",
    "WizardEngine",
    "WizardDefinition",
    "RichContext",
    "WizardSession",
    "StepDefinition",
    "StepType",
    "SessionStatus",
    "ValidationRule",
    "WizardSessionModel",
    "SQLiteSessionStore",
    "utc_now",
    "add_seconds",
    "is_expired",
    "topological_sort",
    "find_path",
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
