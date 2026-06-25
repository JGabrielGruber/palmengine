"""Build behavior-tree structures for transform pipelines."""

from __future__ import annotations

from palm.common.transforms.builder import build_transform_leaves
from palm.core.behavior_tree import BaseNode, RootNode, SequenceNode
from palm.core.transform.engine import TransformEngine
from palm.patterns.pipeline.bindings.definitions.config import PipelineConfig


def build_pipeline_tree(
    name: str,
    config: PipelineConfig,
    *,
    engine: TransformEngine | None = None,
) -> tuple[RootNode, SequenceNode]:
    """Return ``(root, sequence)`` for the given pipeline configuration."""
    shared = engine if engine is not None else TransformEngine()
    leaves: list[BaseNode] = list(build_transform_leaves(config.steps, engine=shared))
    sequence = SequenceNode(f"{name}_sequence", children=leaves)
    root = RootNode(f"{name}_root", child=sequence)
    return root, sequence
