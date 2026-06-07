"""Wizard pattern registration — import this module to wire the app."""

from palm.core.registry import pattern_registry
from palm.patterns._registry import register_builder
from palm.patterns.wizard.builder import build
from palm.patterns.wizard.pattern import WizardPattern

pattern_registry.register("wizard", WizardPattern)
register_builder("wizard", build)