"""
Built-in common transform rules.

Import :mod:`palm.common.transforms.rules.registry` to register rules with
``transform_registry`` (same pattern as pattern app ``registry.py`` modules).
"""

from palm.common.transforms.rules.calculate import CalculateRule
from palm.common.transforms.rules.callable_rule import CallableRule
from palm.common.transforms.rules.conditional import ConditionalRule
from palm.common.transforms.rules.csv_dump import CsvDumpRule
from palm.common.transforms.rules.csv_load import CsvLoadRule
from palm.common.transforms.rules.date_format import DateFormatRule
from palm.common.transforms.rules.date_parse import DateParseRule
from palm.common.transforms.rules.enrich_resource import EnrichResourceRule
from palm.common.transforms.rules.filter_items import FilterItemsRule
from palm.common.transforms.rules.json_dump import JsonDumpRule
from palm.common.transforms.rules.json_load import JsonLoadRule
from palm.common.transforms.rules.jsonpath_extract import JsonpathExtractRule
from palm.common.transforms.rules.jsonpath_set import JsonpathSetRule
from palm.common.transforms.rules.lookup import LookupRule
from palm.common.transforms.rules.map_fields import MapFieldsRule
from palm.common.transforms.rules.parquet_load import ParquetLoadRule
from palm.common.transforms.rules.rename_field import RenameFieldRule
from palm.common.transforms.rules.string_format import StringFormatRule
from palm.common.transforms.rules.toml_load import TomlLoadRule
from palm.common.transforms.rules.xml_load import XmlLoadRule
from palm.common.transforms.rules.yaml_dump import YamlDumpRule
from palm.common.transforms.rules.yaml_load import YamlLoadRule
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
    JsonLoadRule,
    JsonDumpRule,
    CsvLoadRule,
    CsvDumpRule,
    YamlLoadRule,
    YamlDumpRule,
    TomlLoadRule,
    XmlLoadRule,
    ParquetLoadRule,
)

__all__ = [
    "BUILTIN_RULES",
    "CalculateRule",
    "CallableRule",
    "ConditionalRule",
    "CsvDumpRule",
    "CsvLoadRule",
    "DateFormatRule",
    "DateParseRule",
    "EnrichResourceRule",
    "FilterItemsRule",
    "JsonDumpRule",
    "JsonLoadRule",
    "JsonpathExtractRule",
    "JsonpathSetRule",
    "LookupRule",
    "MapFieldsRule",
    "ParquetLoadRule",
    "RenameFieldRule",
    "StringFormatRule",
    "TomlLoadRule",
    "XmlLoadRule",
    "YamlDumpRule",
    "YamlLoadRule",
]
