"""
Transform pipeline runner — apply declarative chains via TransformEngine.
"""

from __future__ import annotations

from typing import Any

from palm.common.transforms.bootstrap import ensure_common_transforms
from palm.common.transforms.spec import TransformPipeline
from palm.core.transform.context import TransformContext
from palm.core.transform.engine import TransformEngine


def resolve_transform_engine(engine: TransformEngine | None = None) -> TransformEngine:
    """Return an initialized engine with core and common rules registered."""
    resolved = engine or TransformEngine()
    if not resolved.is_initialized:
        resolved.initialize()
    ensure_common_transforms()
    return resolved


def apply_pipeline(
    pipeline: TransformPipeline,
    value: Any,
    *,
    engine: TransformEngine | None = None,
    **shared_options: Any,
) -> TransformContext:
    """Apply a declarative pipeline to ``value``."""
    resolved = resolve_transform_engine(engine)
    if len(pipeline.steps) == 1:
        spec = pipeline.steps[0]
        merged = {**shared_options, **spec.options}
        return resolved.apply_auto(spec.rule, value, **merged)

    options_by_rule = {spec.rule: {**shared_options, **spec.options} for spec in pipeline.steps}
    return resolved.apply_chain(
        pipeline.rule_names,
        value,
        options_by_rule=options_by_rule,
    )