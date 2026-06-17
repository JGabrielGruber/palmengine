"""
Wizard step kinds — used for tree construction and backtrack policy.
"""

from __future__ import annotations

from typing import Literal

WizardStepKind = Literal[
    "input",
    "introduction",
    "summary",
    "commit",
    "action",
    "resource",
    "collection",
    "transform",
]

PROTECTED_KINDS: frozenset[WizardStepKind] = frozenset(
    {"introduction", "summary", "commit"},
)
