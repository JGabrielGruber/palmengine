"""Field catalog for analytics describe (schema + exposure.fields)."""

from __future__ import annotations

from typing import Any


def fields_from_schemas(
    *,
    output_schema: dict[str, Any] | None,
    analytics_fields: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return ``[{name, role, type}, ...]`` for UI/agent consumption."""
    if analytics_fields:
        out: list[dict[str, Any]] = []
        schema_types = _property_types(output_schema)
        for item in analytics_fields:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            role = item.get("role") or item.get("x-palm-role")
            typ = item.get("type") or schema_types.get(name)
            out.append({"name": name, "role": role, "type": typ})
        return out

    props = None
    if isinstance(output_schema, dict):
        props = output_schema.get("properties")
    if not isinstance(props, dict):
        return []
    fields: list[dict[str, Any]] = []
    for name, spec in props.items():
        if not isinstance(spec, dict):
            fields.append({"name": str(name), "role": None, "type": None})
            continue
        role = spec.get("x-palm-role") or spec.get("role")
        typ = spec.get("type")
        if isinstance(typ, list):
            typ = next((t for t in typ if t != "null"), typ[0] if typ else None)
        fields.append({"name": str(name), "role": role, "type": typ})
    return fields


def _property_types(output_schema: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(output_schema, dict):
        return {}
    props = output_schema.get("properties")
    if not isinstance(props, dict):
        return {}
    out: dict[str, Any] = {}
    for name, spec in props.items():
        if isinstance(spec, dict):
            out[str(name)] = spec.get("type")
    return out


__all__ = ["fields_from_schemas"]
