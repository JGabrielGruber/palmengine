"""
Build :class:`~palm.core.behavior_tree.nodes.leaf.transform_leaf.TransformLeaf`
nodes from declarative step mappings (flow definitions, patterns).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from palm.common.exceptions import DefinitionBuildError
from palm.core.behavior_tree.nodes.leaf.transform_leaf import TransformLeaf
from palm.core.transform.engine import TransformEngine


@dataclass(frozen=True)
class TransformStepSpec:
    """Declarative transform step for pipelines and flow options."""

    name: str
    source_key: str
    target_key: str | None = None
    rule: str | None = None
    chain: tuple[str, ...] = ()
    scoped: bool = False
    validate_output: bool = True
    batch: bool | None = None
    per_item: bool | None = None
    skip_if_missing: bool = False
    trace_key: str | None = None
    error_key: str | None = None
    options: dict[str, Any] | None = None
    options_by_rule: dict[str, dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise DefinitionBuildError("Transform step requires a non-empty name")
        if not self.source_key:
            raise DefinitionBuildError(
                f"Transform step {self.name!r} requires source_key",
            )
        if not self.rule and not self.chain:
            raise DefinitionBuildError(
                f"Transform step {self.name!r} requires rule or chain",
            )
        if self.rule and self.chain:
            raise DefinitionBuildError(
                f"Transform step {self.name!r} accepts rule or chain, not both",
            )


def transform_step_from_mapping(data: Mapping[str, Any]) -> TransformStepSpec:
    """Parse a transform step dict from a flow definition."""
    name = data.get("name") or data.get("slug")
    if not name:
        raise DefinitionBuildError("Transform step dict requires 'name' or 'slug'")

    source_key = data.get("source_key")
    if not source_key:
        raise DefinitionBuildError(f"Transform step {name!r} requires source_key")

    rule = data.get("rule")
    chain_raw = data.get("chain")
    chain: tuple[str, ...] = ()
    if isinstance(chain_raw, list):
        chain = tuple(str(item) for item in chain_raw)

    options = data.get("options")
    options_by_rule = data.get("options_by_rule")
    trace_key = data.get("trace_key")
    error_key = data.get("error_key")

    return TransformStepSpec(
        name=str(name),
        source_key=str(source_key),
        target_key=str(data["target_key"]) if data.get("target_key") else None,
        rule=str(rule) if rule else None,
        chain=chain,
        scoped=bool(data.get("scoped", False)),
        validate_output=bool(data.get("validate_output", True)),
        batch=data.get("batch"),
        per_item=data.get("per_item"),
        skip_if_missing=bool(data.get("skip_if_missing", False)),
        trace_key=str(trace_key) if trace_key else None,
        error_key=str(error_key) if error_key else None,
        options=dict(options) if isinstance(options, dict) else None,
        options_by_rule=(
            {str(k): dict(v) for k, v in options_by_rule.items()}
            if isinstance(options_by_rule, dict)
            else None
        ),
    )


def build_transform_leaf(
    spec: TransformStepSpec,
    *,
    engine: TransformEngine | None = None,
) -> TransformLeaf:
    """Materialize a :class:`TransformLeaf` from ``spec``."""
    return TransformLeaf(
        spec.name,
        engine=engine,
        source_key=spec.source_key,
        target_key=spec.target_key,
        rule=spec.rule,
        chain=spec.chain or None,
        scoped=spec.scoped,
        validate_output=spec.validate_output,
        batch=spec.batch,
        per_item=spec.per_item,
        options=spec.options,
        options_by_rule=spec.options_by_rule,
        skip_if_missing=spec.skip_if_missing,
        trace_key=spec.trace_key,
        error_key=spec.error_key,
    )


def build_transform_leaves(
    steps: Sequence[TransformStepSpec | Mapping[str, Any]],
    *,
    engine: TransformEngine | None = None,
) -> list[TransformLeaf]:
    """Build transform leaves from specs or mapping dicts."""
    shared = engine if engine is not None else TransformEngine()
    if not shared.is_initialized:
        shared.initialize()
    leaves: list[TransformLeaf] = []
    for step in steps:
        spec = step if isinstance(step, TransformStepSpec) else transform_step_from_mapping(step)
        leaves.append(build_transform_leaf(spec, engine=shared))
    return leaves
