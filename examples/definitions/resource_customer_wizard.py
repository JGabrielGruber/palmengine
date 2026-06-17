"""
Resource customer wizard — input step + declarative resource step.

Demonstrates ``step_kind: resource`` with ``resource_ref`` and state binding.
Requires ``fetch-customer`` from ``fetch_customer.py`` (autoloaded separately).
"""

from __future__ import annotations

from palm.definitions import FlowDefinition

RESOURCE_CUSTOMER_WIZARD_FLOW = FlowDefinition(
    id="flow-resource-customer-wizard",
    name="resource-customer-wizard",
    pattern="wizard",
    options={
        "include_summary": True,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "customer_id",
                "title": "Customer ID",
                "prompt": "Enter the customer id to load",
                "validation": [{"rule": "not_empty"}],
            },
            {
                "slug": "get-customer",
                "title": "Load Customer",
                "step_kind": "resource",
                "resource_ref": "fetch-customer",
                "params": {"customer_id": "{{ state.customer_id }}"},
                "output_key": "customer_data",
            },
        ],
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    if callable(save_flow):
        save_flow(RESOURCE_CUSTOMER_WIZARD_FLOW)