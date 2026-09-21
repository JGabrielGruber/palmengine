"""
Django-style autoloading for common transform rules.

``INSTALLED_TRANSFORMS`` is the catalog of real rules.
The composition record names which rules the install stroke registers (0.72.4).
Importing a rule module does not register it. Each module exposes ``register()``.
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


def autoload(names: tuple[str, ...]) -> None:
    """Register the named built-in rules."""
    for name in names:
        module = importlib.import_module(f"palm.common.transforms.rules.{name}")
        module.register()
