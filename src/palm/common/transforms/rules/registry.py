"""Built-in transform rule registration — import to wire common rules."""

from __future__ import annotations

from palm.common.transforms.registration import register_transform
from palm.common.transforms.rules.append_item import AppendItemRule
from palm.common.transforms.rules.calculate import CalculateRule
from palm.common.transforms.rules.callable_rule import CallableRule
from palm.common.transforms.rules.conditional import ConditionalRule
from palm.common.transforms.rules.count_by import CountByRule
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
from palm.common.transforms.rules.put_resource import PutResourceRule
from palm.common.transforms.rules.rename_field import RenameFieldRule
from palm.common.transforms.rules.string_format import StringFormatRule
from palm.common.transforms.rules.toml_load import TomlLoadRule
from palm.common.transforms.rules.xml_load import XmlLoadRule
from palm.common.transforms.rules.yaml_dump import YamlDumpRule
from palm.common.transforms.rules.yaml_load import YamlLoadRule


def register_builtin_rules() -> None:
    """Register built-in common rules (idempotent via ``transform_registry``)."""
    register_transform("rename_field", RenameFieldRule)
    register_transform("map_fields", MapFieldsRule)
    register_transform("append_item", AppendItemRule)
    register_transform("put_resource", PutResourceRule)
    register_transform("filter_items", FilterItemsRule)
    register_transform("count_by", CountByRule)
    register_transform("callable", CallableRule)
    register_transform("string_format", StringFormatRule)
    register_transform("jsonpath_extract", JsonpathExtractRule)
    register_transform("jsonpath_set", JsonpathSetRule)
    register_transform("calculate", CalculateRule)
    register_transform("enrich_resource", EnrichResourceRule)
    register_transform("date_format", DateFormatRule)
    register_transform("date_parse", DateParseRule)
    register_transform("lookup", LookupRule)
    register_transform("conditional", ConditionalRule)
    register_transform("json_load", JsonLoadRule)
    register_transform("json_dump", JsonDumpRule)
    register_transform("csv_load", CsvLoadRule)
    register_transform("csv_dump", CsvDumpRule)
    register_transform("yaml_load", YamlLoadRule)
    register_transform("yaml_dump", YamlDumpRule)
    register_transform("toml_load", TomlLoadRule)
    register_transform("xml_load", XmlLoadRule)
    register_transform("parquet_load", ParquetLoadRule)


register_builtin_rules()
