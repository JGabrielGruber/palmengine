"""
Interactive wizard pattern — multi-step flows with backtracking and events.
"""

from palm.core.registry import pattern_registry
from palm.patterns.wizard.commit import (
    CommitContext,
    CommitRegistry,
    CommitResult,
    default_commit_registry,
)
from palm.patterns.wizard.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.pattern import WizardPattern, default_wizard_config
from palm.patterns.wizard.validation import (
    StepValidationRule,
    ValidationRegistry,
    default_validation_registry,
    validate_step_value,
)

pattern_registry.register("wizard", WizardPattern)

__all__ = [
    "CommitContext",
    "CommitRegistry",
    "CommitResult",
    "StepValidationRule",
    "ValidationRegistry",
    "WizardConfig",
    "WizardEventType",
    "WizardKeys",
    "WizardPattern",
    "WizardStepConfig",
    "default_commit_registry",
    "default_validation_registry",
    "default_wizard_config",
    "validate_step_value",
]