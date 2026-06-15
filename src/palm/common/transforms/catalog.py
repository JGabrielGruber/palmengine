"""
Built-in transform rule catalog — names and short descriptions for docs and ``palm doctor``.
"""

from __future__ import annotations

TRANSFORM_CATALOG: dict[str, str] = {
    "rename_field": "Rename one key in a mapping",
    "map_fields": "Remap multiple keys in a mapping",
    "filter_items": "Filter a list of mappings by field predicates",
    "callable": "Apply a Python callable to a value or list",
    "string_format": "Template, case, and inline date formatting for strings",
    "jsonpath_extract": "Read a nested value via dot path (e.g. user.profile.name)",
    "jsonpath_set": "Write a nested value via dot path on a mapping copy",
    "calculate": "Evaluate a safe arithmetic expression with variables",
    "enrich_resource": "Fetch external data via ResourceEngine and merge into payload",
    "date_format": "Format dates/datetimes/ISO strings with strftime patterns",
    "date_parse": "Parse date strings into ISO date or datetime strings",
    "lookup": "Map a key through a static lookup table with optional default",
    "conditional": "Return then/else values based on equals, numeric, or truthy predicates",
}


def transform_description(name: str) -> str:
    """Return the catalog description for ``name``, or a generic fallback."""
    return TRANSFORM_CATALOG.get(name, "Registered transform rule")