"""
Shared transform coordination — built-in rules and registration helpers.

Import this package (or call :func:`autoload`) to register common rules in
``transform_registry``. Core stays pure; concrete rules live here and in
pattern packages.
"""

from palm.common.transforms._apps import INSTALLED_TRANSFORMS, autoload
from palm.common.transforms.catalog import TRANSFORM_CATALOG, transform_description
from palm.common.transforms.builder import (
    TransformStepSpec,
    build_transform_leaf,
    build_transform_leaves,
    transform_step_from_mapping,
)
from palm.common.transforms.execution import (
    TransformExecutor,
    apply_transform,
    apply_transform_to_state,
    default_executor,
)
from palm.common.transforms.registration import (
    has_transform,
    register_transform,
    register_transforms,
    registered_transform_names,
    registered_transforms,
    transform_rule,
)
from palm.common.transforms.preview import preview_value
from palm.common.transforms.rules import (
    BUILTIN_RULES,
    CalculateRule,
    CallableRule,
    ConditionalRule,
    DateFormatRule,
    DateParseRule,
    EnrichResourceRule,
    FilterItemsRule,
    JsonpathExtractRule,
    JsonpathSetRule,
    LookupRule,
    MapFieldsRule,
    RenameFieldRule,
    StringFormatRule,
)

autoload()

__all__ = [
    "BUILTIN_RULES",
    "CalculateRule",
    "CallableRule",
    "ConditionalRule",
    "DateFormatRule",
    "DateParseRule",
    "EnrichResourceRule",
    "FilterItemsRule",
    "INSTALLED_TRANSFORMS",
    "JsonpathExtractRule",
    "JsonpathSetRule",
    "LookupRule",
    "MapFieldsRule",
    "RenameFieldRule",
    "StringFormatRule",
    "TRANSFORM_CATALOG",
    "preview_value",
    "transform_description",
    "TransformExecutor",
    "TransformStepSpec",
    "apply_transform",
    "apply_transform_to_state",
    "autoload",
    "build_transform_leaf",
    "build_transform_leaves",
    "transform_step_from_mapping",
    "default_executor",
    "has_transform",
    "register_transform",
    "register_transforms",
    "registered_transform_names",
    "registered_transforms",
    "transform_rule",
]
