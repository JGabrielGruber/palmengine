"""
Django-style autoloading for common transform rules.

Each entry in ``INSTALLED_TRANSFORMS`` maps to a built-in rule registered via
``palm.common.transforms.rules.registry``.
"""

from __future__ import annotations

import importlib

INSTALLED_TRANSFORMS: tuple[str, ...] = (
    "rename_field",
    "map_fields",
    "append_item",
    "put_resource",
    "filter_items",
    "count_by",
    "callable",
    "string_format",
    "jsonpath_extract",
    "jsonpath_set",
    "calculate",
    "enrich_resource",
    "date_format",
    "date_parse",
    "lookup",
    "conditional",
    "json_load",
    "json_dump",
    "csv_load",
    "csv_dump",
    "yaml_load",
    "yaml_dump",
    "toml_load",
    "xml_load",
    # parquet_load is intention-only (ST-004); not auto-registered
)

# Not in default install — package may still exist for future pyarrow work.
INTENTION_TRANSFORMS: tuple[str, ...] = ("parquet_load",)


def autoload() -> None:
    """Ensure built-in rule modules are loaded and registry entries exist."""
    importlib.import_module("palm.common.transforms.rules.registry")
    from palm.common.transforms.rules.registry import register_builtin_rules

    register_builtin_rules()
