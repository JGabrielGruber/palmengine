"""
PipelinePattern — sequential transform steps driven by a behavior tree.
"""

from __future__ import annotations

from palm.core.behavior_tree import BasePattern, PatternStatus, RootNode, SequenceNode
from palm.core.context import BaseState
from palm.core.resource.engine import ResourceEngine
from palm.core.transform.engine import TransformEngine
from palm.patterns.pipeline.bindings.behavior_tree.tree import build_pipeline_tree
from palm.patterns.pipeline.bindings.definitions.config import PipelineConfig


class PipelinePattern(BasePattern):
    """
    Run an ordered list of :class:`~palm.core.behavior_tree.nodes.leaf.transform_leaf.TransformLeaf`
    steps. Ideal for ETL normalize stages, wizard action chains, and data prep flows
    declared in :class:`~palm.definitions.flow.FlowDefinition` options.
    """

    def __init__(
        self,
        *,
        name: str = "pipeline",
        config: PipelineConfig | None = None,
        transform_engine: TransformEngine | None = None,
        resource_engine: ResourceEngine | None = None,
    ) -> None:
        super().__init__(name=name)
        if config is None:
            raise ValueError("PipelinePattern requires a PipelineConfig")
        self._config = config
        self._engine = transform_engine if transform_engine is not None else TransformEngine()
        self._resource_engine = resource_engine
        self._seeded = False
        self._root: RootNode
        self._sequence: SequenceNode
        self._root, self._sequence = build_pipeline_tree(
            name,
            config,
            engine=self._engine,
            resource_engine=self._resource_engine,
        )

    @property
    def config(self) -> PipelineConfig:
        return self._config

    @property
    def root(self) -> RootNode:
        return self._root

    def tick(self, state: BaseState) -> PatternStatus:
        self._seed_initial_state(state)
        return self._root.tick(state)

    def reset(self) -> None:
        self._seeded = False
        self._root.reset()

    def _seed_initial_state(self, state: BaseState) -> None:
        if self._seeded or not self._config.initial_state:
            return
        for key, value in self._config.initial_state.items():
            if not state.has(key):
                state.set(key, value)
        self._seeded = True
