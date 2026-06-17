"""
Data ingestion — validation, REST resource action, summary, and commit.

Models registering a dataset: collect metadata, verify an external resource,
then commit registration. The process also includes an ETL flow placeholder
for multi-flow pipelines.
"""

from __future__ import annotations

from typing import Any

from palm.definitions import FlowDefinition, ProcessDefinition, ResourceDefinition
from palm.patterns.wizard.handler import CommitResult, default_commit_registry

REST_HEALTH_RESOURCE = ResourceDefinition(
    id="resource-rest-health",
    name="rest-health",
    provider="rest",
    action="fetch",
    resource_id="health/check",
)

INGEST_WIZARD_FLOW = FlowDefinition(
    id="flow-ingest-wizard",
    name="ingest-wizard",
    pattern="wizard",
    options={
        "include_summary": True,
        "include_commit": True,
        "commit_hook": "register_dataset",
        "allow_backtrack": True,
        "steps": [
            {
                "slug": "dataset_name",
                "title": "Dataset Name",
                "prompt": "Name for this dataset (e.g. sales_q1)",
                "validation": [
                    {"rule": "min_length", "params": {"min": 3}},
                    {
                        "rule": "regex",
                        "params": {
                            "pattern": r"^[a-z][a-z0-9_]*$",
                            "message": "Use lowercase letters, digits, and underscores",
                        },
                    },
                ],
            },
            {
                "slug": "source_uri",
                "title": "Source URI",
                "prompt": "Where does the data live? (s3://bucket/path or https://...)",
                "validation": [{"rule": "not_empty"}],
            },
            {
                "slug": "verify_source",
                "title": "Verify Source",
                "prompt": "Verify REST connectivity by fetching a health check sample",
                "step_kind": "resource",
                "resource_ref": "rest-health",
                "output_key": "verify_source",
            },
        ],
    },
)

INGEST_ETL_FLOW = FlowDefinition(
    id="flow-ingest-etl",
    name="ingest-etl",
    pattern="etl",
    options={"name": "ingest-etl"},
)

DATA_INGESTION_PROCESS = ProcessDefinition(
    id="proc-data-ingestion",
    name="data-ingestion",
    flows=[INGEST_WIZARD_FLOW, INGEST_ETL_FLOW],
    metadata={
        "example": True,
        "description": "Dataset registration wizard + ETL pipeline stub",
    },
)


def _register_dataset(ctx: Any) -> CommitResult:
    record = {
        "dataset_name": ctx.answers.get("dataset_name"),
        "source_uri": ctx.answers.get("source_uri"),
        "verified": bool(ctx.answers.get("verify_source")),
    }
    if not record["dataset_name"] or not record["source_uri"]:
        return CommitResult.failure("dataset_name and source_uri are required")
    return CommitResult.success({"dataset": record, "status": "registered"})


def register_definitions(repository: object) -> None:
    default_commit_registry().register("register_dataset", _register_dataset)
    save_resource = getattr(repository, "save_resource", None)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_resource):
        save_resource(REST_HEALTH_RESOURCE)
    if callable(save_flow):
        save_flow(INGEST_WIZARD_FLOW)
        save_flow(INGEST_ETL_FLOW)
    if callable(save_process):
        save_process(DATA_INGESTION_PROCESS)