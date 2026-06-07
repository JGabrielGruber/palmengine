"""
Wizard pattern app — interactive multi-step flows with backtracking and events.

Self-contained subpackage:

- ``pattern.py`` — ``WizardPattern`` implementation
- ``handler.py`` — commit handler registry
- ``builder.py`` / ``options.py`` — definition → pattern materialization
- ``registry.py`` — ``pattern_registry`` wiring
"""

from palm.patterns.wizard import registry as registry  # — side effect
from palm.patterns.wizard.builder import wizard_config_from_options
from palm.patterns.wizard.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.handler import (
    CommitContext,
    CommitRegistry,
    CommitResult,
    default_commit_registry,
)
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.options import parse_wizard_flow_options, wizard_metadata_from_flow
from palm.patterns.wizard.pattern import WizardPattern, default_wizard_config
from palm.patterns.wizard.validation import (
    StepValidationRule,
    ValidationRegistry,
    default_validation_registry,
    validate_step_value,
)

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
    "parse_wizard_flow_options",
    "registry",
    "validate_step_value",
    "wizard_config_from_options",
    "wizard_metadata_from_flow",
]