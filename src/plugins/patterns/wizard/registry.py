"""Wizard pattern registration. Call :func:`register` with the system registries."""

from palm.system.registries import SystemRegistries
from plugins.patterns.wizard.bindings.definitions.builder import build
from plugins.patterns.wizard.bindings.instances.submission import wizard_submission_metadata
from plugins.patterns.wizard.pattern import WizardPattern


def register(registries: SystemRegistries) -> None:
    """Register the wizard pattern and its builder on ``registries``."""
    registries.require("pattern").register("wizard", WizardPattern)
    registries.require("pattern_builder").register("wizard", build)
    if "submission_metadata" in registries.names():
        registries.require("submission_metadata").register("wizard", wizard_submission_metadata)


__all__ = ["register"]
