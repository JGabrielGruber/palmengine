"""Re-export step registry from the phases package."""

from palm.patterns.wizard.phases.registry import (
    WizardStepBuildContext,
    WizardStepKindRegistry,
    default_wizard_step_registry,
    register_builtin_wizard_step_kinds,
)

__all__ = [
    "WizardStepBuildContext",
    "WizardStepKindRegistry",
    "default_wizard_step_registry",
    "register_builtin_wizard_step_kinds",
]