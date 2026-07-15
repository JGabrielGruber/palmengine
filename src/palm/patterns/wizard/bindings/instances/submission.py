"""
Wizard flow submission extensions — job metadata enrichment for orchestration.

Registered via :func:`~palm.common.patterns._registry.register_submission_metadata` so
``palm.common.executions.flow_submission`` stays pattern-agnostic.
"""

from __future__ import annotations

from typing import Any

from palm.definitions.flow import FlowDefinition
from palm.patterns.wizard.bindings.definitions.options import wizard_metadata_from_flow


def wizard_submission_metadata(flow: FlowDefinition) -> dict[str, Any]:
    """Attach wizard-specific keys to job metadata during flow submission."""
    if not flow.options:
        return {}
    meta = wizard_metadata_from_flow(flow.options)
    return {"wizard": meta} if meta else {}
