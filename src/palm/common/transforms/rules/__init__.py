"""
Built-in common transform rules.

Import :mod:`palm.common.transforms.rules.registry` to register rules with
``transform_registry`` (same pattern as pattern app ``registry.py`` modules).
"""

from palm.common.transforms.rules.callable_rule import CallableRule
from palm.common.transforms.rules.filter_items import FilterItemsRule
from palm.common.transforms.rules.map_fields import MapFieldsRule
from palm.common.transforms.rules.rename_field import RenameFieldRule
from palm.common.transforms.rules.string_format import StringFormatRule
from palm.core.transform.base import BaseTransformRule

BUILTIN_RULES: tuple[type[BaseTransformRule], ...] = (
    RenameFieldRule,
    MapFieldsRule,
    FilterItemsRule,
    CallableRule,
    StringFormatRule,
)

__all__ = [
    "BUILTIN_RULES",
    "CallableRule",
    "FilterItemsRule",
    "MapFieldsRule",
    "RenameFieldRule",
    "StringFormatRule",
]
