"""Wizard pattern registration. Call :func:`register` with the system registries."""

from palm.common.persistence.instance_sync import InstanceSyncHooks
from palm.system.registries import SystemRegistries
from plugins.patterns.wizard.bindings.bridges import wizard_interactive_hooks
from plugins.patterns.wizard.bindings.definitions.builder import build
from plugins.patterns.wizard.bindings.instances.persistence import (
    extract_instance_fields_from_job,
    prepare_wizard_resume_state,
)
from plugins.patterns.wizard.bindings.instances.submission import wizard_submission_metadata
from plugins.patterns.wizard.bindings.read_model import build_wizard_view
from plugins.patterns.wizard.flow.extensions.registry import register_builtin_wizard_step_kinds
from plugins.patterns.wizard.pattern import WizardPattern


def register(registries: SystemRegistries) -> None:
    """Register the wizard pattern and its builder on ``registries``."""
    registries.require("pattern").register("wizard", WizardPattern)
    registries.require("pattern_builder").register("wizard", build)
    if "wizard_step" in registries.names():
        register_builtin_wizard_step_kinds(registries.require("wizard_step"))
    if "submission_metadata" in registries.names():
        registries.require("submission_metadata").register("wizard", wizard_submission_metadata)
    if "instance_sync" in registries.names():
        registries.require("instance_sync").register(
            "wizard",
            InstanceSyncHooks(
                fields=extract_instance_fields_from_job,
                resume=prepare_wizard_resume_state,
            ),
        )
    if "interactive_runtime" in registries.names():
        registries.require("interactive_runtime").register(
            "wizard",
            wizard_interactive_hooks(),
        )
    if "read_model_builder" in registries.names():
        registries.require("read_model_builder").register("wizard", build_wizard_view)


__all__ = ["register"]
