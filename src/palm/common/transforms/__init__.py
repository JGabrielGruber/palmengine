"""
Shared transform coordination — built-in rules and registration helpers.

Import this package (or call :func:`autoload`) to register common rules in
``transform_registry``. Core stays pure; concrete rules live here and in
pattern packages.
"""

from palm.common.transforms._apps import INSTALLED_TRANSFORMS, autoload
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
from palm.common.transforms.rules import (
    BUILTIN_RULES,
    CallableRule,
    FilterItemsRule,
    MapFieldsRule,
    RenameFieldRule,
)

autoload()

__all__ = [
    "BUILTIN_RULES",
    "CallableRule",
    "FilterItemsRule",
    "INSTALLED_TRANSFORMS",
    "MapFieldsRule",
    "RenameFieldRule",
    "TransformExecutor",
    "apply_transform",
    "apply_transform_to_state",
    "autoload",
    "default_executor",
    "has_transform",
    "register_transform",
    "register_transforms",
    "registered_transform_names",
    "registered_transforms",
    "transform_rule",
]
