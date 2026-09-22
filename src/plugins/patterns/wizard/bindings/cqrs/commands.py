"""Wizard CQRS command types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.cqrs.command import Command


@dataclass(frozen=True)
class SubmitWizardCommand(Command):
    """Submit a wizard flow — always resolves to ``pattern='wizard'``."""

    body: dict[str, Any]
    runtime_name: str | None = None


@dataclass(frozen=True)
class ProvideWizardInputCommand(Command):
    """Deliver interactive input to a wizard instance."""

    instance_id: str
    value: Any
    runtime_name: str | None = None


@dataclass(frozen=True)
class RequestWizardBacktrackCommand(Command):
    """Backtrack a wizard to a prior step (defaults to the previous step)."""

    instance_id: str
    to_step: str | None = None
    runtime_name: str | None = None


__all__ = [
    "ProvideWizardInputCommand",
    "RequestWizardBacktrackCommand",
    "SubmitWizardCommand",
]
