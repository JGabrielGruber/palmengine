"""
Compositional demo — parent wizard invokes a child flow via the ``palm`` provider.

Demonstrates Palm calling Palm: a confirmation step submits ``ingest-etl`` as a
child job and stores the correlation payload on the blackboard.
Requires ``ingest-etl`` from ``data_ingestion.py``.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ResourceDefinition

SUBMIT_INGEST_ETL_RESOURCE = ResourceDefinition(
    id="resource-submit-ingest-etl",
    name="submit-ingest-etl",
    provider="palm",
    action="submit_flow",
    resource_id="flow:ingest-etl",
    params={"wait": True, "wait_timeout": 30},
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
                "slug": "run-etl",
                "title": "Run Child ETL",
                "prompt": "Submit the ingest-etl child flow now?",
                "step_kind": "resource",
                "resource_ref": "submit-ingest-etl",
                "output_key": "child_job",
            },
        ],
    },
)


def register_definitions(repository: object) -> None:
    save_resource = getattr(repository, "save_resource", None)
    save_flow = getattr(repository, "save_flow", None)
    if callable(save_resource):
        save_resource(SUBMIT_INGEST_ETL_RESOURCE)
    if callable(save_flow):
        save_flow(COMPOSITIONAL_PARENT_FLOW)