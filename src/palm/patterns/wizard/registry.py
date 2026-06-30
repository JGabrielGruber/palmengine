"""Wizard pattern registration — import this module to wire the app."""

from palm.core.registry import pattern_registry
from palm.patterns._registry import (
    register_builder,
    register_instance_sync,
    register_submission_metadata,
)
from palm.patterns.wizard.app import wizard_app
from palm.patterns.wizard.bindings.definitions.builder import build
from palm.patterns.wizard.bindings.instances.persistence import (
    extract_instance_fields_from_job,
    prepare_wizard_resume_state,
)
from palm.patterns.wizard.bindings.instances.submission import wizard_submission_metadata
from palm.patterns.wizard.pattern import WizardPattern

pattern_registry.register("wizard", WizardPattern)
register_builder("wizard", build)
register_instance_sync(
    "wizard",
    fields=extract_instance_fields_from_job,
    resume=prepare_wizard_resume_state,
)
register_submission_metadata("wizard", wizard_submission_metadata)
wizard_app.register()
