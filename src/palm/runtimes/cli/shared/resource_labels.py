"""Resource catalog labels — compact definition summaries."""

from __future__ import annotations

from typing import Any


def resource_detail_label(resource: Any) -> str:
    """Compact catalog label for a resource definition."""
    parts: list[str] = []
    if resource.resource_id:
        parts.append(str(resource.resource_id))
    if resource.params:
        parts.append(f"{len(resource.params)} param(s)")
    if resource.has_schemas:
        schema_bits: list[str] = []
        if resource.has_input_schema:
            schema_bits.append("in")
        if resource.has_output_schema:
            schema_bits.append("out")
        parts.append(f"schema:{'+'.join(schema_bits)}")
    return ", ".join(parts) if parts else "—"