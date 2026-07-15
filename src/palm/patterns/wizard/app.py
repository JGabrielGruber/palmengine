"""
Wizard app manifest — declares Palm layer dependencies and registry hooks.

Read this file first to understand which Palm subsystems the wizard pattern dogfoods.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp
from palm.common.patterns._registry import (
    CqrsContributor,
    DesignContributorHook,
    McpContributor,
    register_cqrs_contributor,
    register_design_contributor_hook,
    register_mcp_contributor,
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
from palm.patterns.wizard.bindings.cqrs.schemas import (
    WIZARD_COMMAND_SCHEMAS,
    WIZARD_QUERY_SCHEMAS,
)
from palm.patterns.wizard.bindings.mcp import register_wizard_mcp_tools


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
        "mcp_contributor",
        "design_contributor",
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
                command_schemas=WIZARD_COMMAND_SCHEMAS,
                query_schemas=WIZARD_QUERY_SCHEMAS,
                instance_status_query=GetWizardStatusQuery,
                handle_command=handle_wizard_command,
                handle_query=handle_wizard_query,
            )
        )
        register_mcp_contributor(
            McpContributor(pattern_name="wizard", register=register_wizard_mcp_tools)
        )
        from palm.patterns.wizard.bindings.design import register_wizard_design_contributor

        register_design_contributor_hook(
            DesignContributorHook(
                pattern_name="wizard",
                register=register_wizard_design_contributor,
            )
        )


wizard_app = WizardApp()

__all__ = ["WizardApp", "wizard_app"]
