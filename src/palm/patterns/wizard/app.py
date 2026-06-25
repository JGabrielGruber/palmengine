"""
Wizard app manifest — declares Palm layer dependencies and registry hooks.

Read this file first to understand which Palm subsystems the wizard pattern dogfoods.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp
from palm.patterns._registry import (
    CqrsContributor,
    register_cqrs_contributor,
    register_projection_factory,
)
from palm.patterns.wizard.bindings.bridges import register_wizard_bridges
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
    SubmitWizardCommand,
)
from palm.patterns.wizard.bindings.cqrs.handlers import (
    handle_wizard_command,
    handle_wizard_query,
)
from palm.patterns.wizard.bindings.cqrs.projection import WizardProgressProjection
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    GetWizardStatusQuery,
    ListWizardProgressQuery,
)


class WizardApp(PatternApp):
    name = "wizard"
    label = "Interactive multi-step flow"
    palm_layers = (
        "core.behavior_tree",
        "core.context",
        "core.event",
        "core.resource",
        "core.orchestration",
        "common.patterns",
        "common.transforms",
        "common.resource",
        "common.compensation",
        "definitions.flow",
        "instances",
    )
    registry_hooks = (
        "builder",
        "instance_sync",
        "submission_metadata",
        "interactive_runtime",
        "child_wait",
        "read_model_builder",
        "projection_factory",
        "cqrs_contributor",
    )

    def ready(self) -> None:
        register_wizard_bridges()
        register_projection_factory("wizard", WizardProgressProjection)
        register_cqrs_contributor(
            CqrsContributor(
                pattern_name="wizard",
                command_types=(
                    SubmitWizardCommand,
                    ProvideWizardInputCommand,
                    RequestWizardBacktrackCommand,
                ),
                query_types=(
                    GetWizardProgressQuery,
                    GetWizardStatusQuery,
                    ListWizardProgressQuery,
                ),
                handle_command=handle_wizard_command,
                handle_query=handle_wizard_query,
            )
        )


wizard_app = WizardApp()

__all__ = ["WizardApp", "wizard_app"]