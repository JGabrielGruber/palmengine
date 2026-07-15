"""
Built-in transform rule catalog — names and short descriptions for docs and ``palm doctor``.
"""

from __future__ import annotations

TRANSFORM_CATALOG: dict[str, str] = {
    "rename_field": "Rename one key in a mapping",
    "map_fields": "Remap multiple keys in a mapping",
    "append_item": "Append an item to a list in state (cap, dedup, prepend)",
    "put_resource": "Persist state data via resource invoke (default put)",
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
    "json_load": "Parse JSON text or bytes into dict/list",
    "json_dump": "Serialize dict/list to a JSON string",
    "csv_load": "Parse CSV text into a list of row dicts (header-aware)",
    "csv_dump": "Serialize a list of row dicts to CSV text",
    "yaml_load": "Parse YAML text into structured data (requires PyYAML)",
    "yaml_dump": "Serialize data to YAML text (requires PyYAML)",
    "toml_load": "Parse TOML text or bytes into a mapping (stdlib tomllib)",
    "xml_load": "Parse XML text into nested mappings (stdlib ElementTree)",
    "parquet_load": "Placeholder for Parquet — register a custom rule with pyarrow",
}


def transform_description(name: str) -> str:
    """Return the catalog description for ``name``, or a generic fallback."""
    return TRANSFORM_CATALOG.get(name, "Registered transform rule")
