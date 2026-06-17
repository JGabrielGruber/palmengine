"""
Fetch customer — example resource definition for REST provider lookup.

Demonstrates declarative resource contracts stored in the definition repository.
Invoke via CLI: ``palm resource invoke fetch-customer customer_id=cust-42``
"""

from __future__ import annotations

from palm.definitions import ResourceDefinition

FETCH_CUSTOMER_RESOURCE = ResourceDefinition(
    id="resource-fetch-customer",
    name="fetch-customer",
    provider="rest",
    action="fetch",
    resource_id="customers/{customer_id}",
    params={"customer_id": "{{ state.customer_id }}"},
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
        },
        "required": ["customer_id"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "email": {"type": "string"},
        },
    },
    output_key="customer",
    metadata={
        "example": True,
        "description": "Load customer record before commit",
        "tags": ["crm", "read"],
    },
)


def register_definitions(repository: object) -> None:
    save_resource = getattr(repository, "save_resource", None)
    if callable(save_resource):
        save_resource(FETCH_CUSTOMER_RESOURCE)