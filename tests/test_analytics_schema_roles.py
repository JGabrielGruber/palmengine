"""0.36 — field roles for describe."""

from __future__ import annotations

from palm.services.analytics.schema_roles import fields_from_schemas


def test_json_schema_properties_become_fields() -> None:
    fields = fields_from_schemas(
        output_schema={
            "type": "object",
            "properties": {
                "day": {"type": "string", "x-palm-role": "dimension"},
                "revenue": {"type": "number", "x-palm-role": "measure"},
            },
        },
        analytics_fields=None,
    )
    by_name = {f["name"]: f for f in fields}
    assert by_name["day"]["role"] == "dimension"
    assert by_name["revenue"]["role"] == "measure"


def test_analytics_fields_override() -> None:
    fields = fields_from_schemas(
        output_schema=None,
        analytics_fields=[{"name": "priority", "role": "dimension"}],
    )
    assert fields[0]["name"] == "priority"
    assert fields[0]["role"] == "dimension"
