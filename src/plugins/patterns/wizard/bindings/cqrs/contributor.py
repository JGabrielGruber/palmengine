"""Wizard CQRS contributor record.

``register`` writes this record onto the system table when that table is
installed. ``WizardApp.ready`` writes the same record onto the process map.
"""

from __future__ import annotations

from palm.common.patterns._registry import CqrsContributor
from plugins.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
    SubmitWizardCommand,
)
from plugins.patterns.wizard.bindings.cqrs.handlers import (
    handle_wizard_command,
    handle_wizard_query,
)
from plugins.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    GetWizardStatusQuery,
    ListWizardProgressQuery,
)
from plugins.patterns.wizard.bindings.cqrs.schemas import (
    WIZARD_COMMAND_SCHEMAS,
    WIZARD_QUERY_SCHEMAS,
)


def wizard_cqrs_contributor() -> CqrsContributor:
    """Return the wizard command and query record."""

    return CqrsContributor(
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


__all__ = ["wizard_cqrs_contributor"]
