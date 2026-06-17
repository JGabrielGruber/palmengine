"""
Compositional demo — Palm calling Palm with nesting and remote patterns.

Demonstrates:
- Parent wizard invoking a child ETL flow via the ``palm`` provider
- Two-level nesting (parent → ETL → nested health check resource)
- Remote invocation shape (``remote_url`` param — for federated ServerRuntime)

Requires ``ingest-etl`` and ``rest-health`` from sibling examples.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ResourceDefinition

REST_HEALTH_RESOURCE = ResourceDefinition(
    id="resource-rest-health",
    name="rest-health",
    provider="rest",
    action="fetch",
    resource_id="health/check",
)

SUBMIT_INGEST_ETL_RESOURCE = ResourceDefinition(
    id="resource-submit-ingest-etl",
    name="submit-ingest-etl",
    provider="palm",
    action="submit_flow",
    resource_id="flow:ingest-etl",
    params={"wait": True, "wait_timeout": 30},
)

CHECK_HEALTH_RESOURCE = ResourceDefinition(
    id="resource-check-health",
    name="check-health",
    provider="rest",
    action="fetch",
    resource_id="health/check",
)

NESTED_COMPOSITION_FLOW = FlowDefinition(
    id="flow-nested-composition",
    name="nested-composition",
    pattern="wizard",
    options={
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "preflight",
                "title": "Preflight Check",
                "step_kind": "resource",
                "resource_ref": "check-health",
                "output_key": "health",
            },
            {
                "slug": "run-etl",
                "title": "Run Child ETL",
                "step_kind": "resource",
                "resource_ref": "submit-ingest-etl",
                "output_key": "child_job",
            },
        ],
    },
)

COMPOSITIONAL_PARENT_FLOW = FlowDefinition(
    id="flow-compositional-parent",
    name="compositional-parent",
    pattern="wizard",
    options={
        "include_summary": True,
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "orchestrate",
                "title": "Orchestrate Child Flows",
                "prompt": "Run nested-composition child wizard?",
                "step_kind": "resource",
                "resource_ref": "submit-nested-composition",
                "output_key": "nested_job",
            },
        ],
    },
)

SUBMIT_NESTED_COMPOSITION_RESOURCE = ResourceDefinition(
    id="resource-submit-nested-composition",
    name="submit-nested-composition",
    provider="palm",
    action="submit_flow",
    resource_id="flow:nested-composition",
    params={"wait": True, "wait_timeout": 45},
)

SUBMIT_INGEST_ETL_REMOTE_RESOURCE = ResourceDefinition(
    id="resource-submit-ingest-etl-remote",
    name="submit-ingest-etl-remote",
    provider="palm",
    action="submit_flow",
    resource_id="flow:ingest-etl",
    params={
        "wait": True,
        "wait_timeout": 30,
        "remote_url": "{{ state.remote_url }}",
    },
    metadata={
        "example": True,
        "description": "Federated pattern — bind remote_url on state before invoke",
    },
)


def register_definitions(repository: object) -> None:
    save_resource = getattr(repository, "save_resource", None)
    save_flow = getattr(repository, "save_flow", None)
    if callable(save_resource):
        save_resource(REST_HEALTH_RESOURCE)
        save_resource(CHECK_HEALTH_RESOURCE)
        save_resource(SUBMIT_INGEST_ETL_RESOURCE)
        save_resource(SUBMIT_NESTED_COMPOSITION_RESOURCE)
        save_resource(SUBMIT_INGEST_ETL_REMOTE_RESOURCE)
    if callable(save_flow):
        save_flow(NESTED_COMPOSITION_FLOW)
        save_flow(COMPOSITIONAL_PARENT_FLOW)
    register_compensation_handlers()


def register_compensation_handlers() -> None:
    """Optional undo handlers for mutating compositional resource invokes."""
    from palm.common.compensation import (
        CompensationContext,
        CompensationResult,
        default_compensation_registry,
    )

    def undo_child_etl(ctx: CompensationContext) -> CompensationResult:
        job_id = ctx.payload.get("resource_id") or ctx.job_id
        return CompensationResult.success({"cancelled_child": job_id})

    registry = default_compensation_registry()
    registry.register_for_resource("submit-ingest-etl", undo_child_etl)
    registry.register_for_resource("submit-nested-composition", undo_child_etl)
