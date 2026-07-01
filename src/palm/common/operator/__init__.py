"""Operator-facing read models — compact inspect and compositional invoke trees."""

from palm.common.operator.compact import compact_job_inspect, compact_wizard_inspect
from palm.common.operator.invoke_tree import build_invoke_tree
from palm.common.operator.view_registry import (
    OperatorViewContext,
    allowed_view_formats,
    build_operator_view,
    normalize_view_format,
    register_operator_view_builder,
)

__all__ = [
    "OperatorViewContext",
    "allowed_view_formats",
    "build_invoke_tree",
    "build_operator_view",
    "compact_job_inspect",
    "compact_wizard_inspect",
    "normalize_view_format",
    "register_operator_view_builder",
]
