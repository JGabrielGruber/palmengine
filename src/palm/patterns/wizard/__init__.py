"""
Interactive wizard pattern — multi-step flows with backtracking and events.
"""

from palm.core.registry import pattern_registry
from palm.patterns.wizard.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.events import WizardEventType
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.pattern import WizardPattern, default_wizard_config

pattern_registry.register("wizard", WizardPattern)

__all__ = [
    "WizardConfig",
    "WizardEventType",
    "WizardKeys",
    "WizardPattern",
    "WizardStepConfig",
    "default_wizard_config",
]