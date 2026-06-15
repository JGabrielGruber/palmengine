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
    "filter_items",
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
)


def autoload() -> None:
    """Ensure built-in rule modules are loaded and registry entries exist."""
    importlib.import_module("palm.common.transforms.rules.registry")
    from palm.common.transforms.rules.registry import register_builtin_rules

    register_builtin_rules()