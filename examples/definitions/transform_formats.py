"""
Transform formats demo — JSON ingest, reshape, CSV export.

Demonstrates serialization rules in a pipeline:

1. ``json_load`` — parse an API-style JSON payload
2. ``jsonpath_extract`` — pull the records array
3. ``rename_field`` — normalize a column (batch per row)
4. ``csv_dump`` — export as CSV for downstream tools

Try::

    palm flow start transform-formats
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

_RAW_JSON = """\
{
  "meta": {"source": "api"},
  "records": [
    {"first_name": "Ada", "score": 98},
    {"first_name": "Grace", "score": 95}
  ]
}
"""

TRANSFORM_FORMATS_FLOW = FlowDefinition(
    id="flow-transform-formats",
    name="transform-formats",
    pattern="pipeline",
    options={
        "initial_state": {
            "raw_json": _RAW_JSON,
        },
        "steps": [
            {
                "name": "parse_json",
                "source_key": "raw_json",
                "target_key": "payload",
                "rule": "json_load",
            },
            {
                "name": "extract_records",
                "source_key": "payload",
                "target_key": "records",
                "rule": "jsonpath_extract",
                "options": {"path": "records"},
            },
            {
                "name": "normalize_names",
                "source_key": "records",
                "target_key": "records",
                "rule": "rename_field",
                "batch": True,
                "options": {"from_key": "first_name", "to_key": "name"},
            },
            {
                "name": "export_csv",
                "source_key": "records",
                "target_key": "csv_export",
                "rule": "csv_dump",
                "options": {"fieldnames": ["name", "score"]},
            },
        ],
    },
)

TRANSFORM_FORMATS_PROCESS = ProcessDefinition(
    id="proc-transform-formats",
    name="transform-formats",
    flows=[TRANSFORM_FORMATS_FLOW],
    metadata={
        "example": True,
        "description": "json_load → transform → csv_dump pipeline",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(TRANSFORM_FORMATS_FLOW)
    if callable(save_process):
        save_process(TRANSFORM_FORMATS_PROCESS)