"""Built-in transform rule registration — import to wire common rules."""

from __future__ import annotations

from palm.common.transforms.registration import register_transform
from palm.common.transforms.rules.callable_rule import CallableRule
from palm.common.transforms.rules.filter_items import FilterItemsRule
from palm.common.transforms.rules.map_fields import MapFieldsRule
from palm.common.transforms.rules.rename_field import RenameFieldRule


def register_builtin_rules() -> None:
    """Register built-in common rules (idempotent via ``transform_registry``)."""
    register_transform("rename_field", RenameFieldRule)
    register_transform("map_fields", MapFieldsRule)
    register_transform("filter_items", FilterItemsRule)
    register_transform("callable", CallableRule)


register_builtin_rules()
