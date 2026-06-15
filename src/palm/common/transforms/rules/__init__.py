"""
Built-in common transform rules.

Import :mod:`palm.common.transforms.rules.registry` to register rules with
``transform_registry`` (same pattern as pattern app ``registry.py`` modules).
"""

from palm.common.transforms.rules.calculate import CalculateRule
from palm.common.transforms.rules.callable_rule import CallableRule
from palm.common.transforms.rules.conditional import ConditionalRule
from palm.common.transforms.rules.date_format import DateFormatRule
from palm.common.transforms.rules.date_parse import DateParseRule
from palm.common.transforms.rules.enrich_resource import EnrichResourceRule
from palm.common.transforms.rules.filter_items import FilterItemsRule
from palm.common.transforms.rules.jsonpath_extract import JsonpathExtractRule
from palm.common.transforms.rules.jsonpath_set import JsonpathSetRule
from palm.common.transforms.rules.lookup import LookupRule
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
    JsonpathExtractRule,
    JsonpathSetRule,
    CalculateRule,
    EnrichResourceRule,
    DateFormatRule,
    DateParseRule,
    LookupRule,
    ConditionalRule,
)

__all__ = [
    "BUILTIN_RULES",
    "CalculateRule",
    "CallableRule",
    "ConditionalRule",
    "DateFormatRule",
    "DateParseRule",
    "EnrichResourceRule",
    "FilterItemsRule",
    "JsonpathExtractRule",
    "JsonpathSetRule",
    "LookupRule",
    "MapFieldsRule",
    "RenameFieldRule",
    "StringFormatRule",
]