"""Flow extension registries — step kinds and custom phase factories."""

from palm.patterns.wizard.flow.extensions.registry import (
    WizardStepKindRegistry,
    default_wizard_step_registry,
    register_builtin_wizard_step_kinds,
)

__all__ = [
    "WizardStepKindRegistry",
    "default_wizard_step_registry",
    "register_builtin_wizard_step_kinds",
]
