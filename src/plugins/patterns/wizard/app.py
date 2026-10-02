"""
Wizard app manifest — declares Palm layer dependencies and registry hooks.

Read this file first to understand which Palm subsystems the wizard pattern dogfoods.
"""

from __future__ import annotations

from palm.common.patterns.app import PatternApp
from palm.common.patterns._registry import (
    DesignContributorHook,
    McpContributor,
    register_cqrs_contributor,
    register_design_contributor_hook,
    register_mcp_contributor,
    register_projection_factory,
)
from plugins.patterns.wizard.bindings.bridges import register_wizard_bridges
from plugins.patterns.wizard.bindings.cqrs.contributor import wizard_cqrs_contributor
from plugins.patterns.wizard.bindings.cqrs.projection import WizardProgressProjection
from plugins.patterns.wizard.bindings.mcp import register_wizard_mcp_tools


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
        "read_model_builder",
        "projection_factory",
        "cqrs_contributor",
        "mcp_contributor",
        "design_contributor",
    )

    def ready(self) -> None:
        register_wizard_bridges()
        register_projection_factory("wizard", WizardProgressProjection)
        register_cqrs_contributor(wizard_cqrs_contributor())
        register_mcp_contributor(
            McpContributor(pattern_name="wizard", register=register_wizard_mcp_tools)
        )
        from plugins.patterns.wizard.bindings.design import register_wizard_design_contributor

        register_design_contributor_hook(
            DesignContributorHook(
                pattern_name="wizard",
                register=register_wizard_design_contributor,
            )
        )


wizard_app = WizardApp()

__all__ = ["WizardApp", "wizard_app"]
