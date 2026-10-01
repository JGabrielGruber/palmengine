"""A wizard transform step reads the system registry (0.72.10).

The step resolves its rule from the ``transform`` table on that runtime.
A missing name raises. The process-wide transform registry is not a fallback.
"""

from __future__ import annotations

import pytest
from bundles.minimal.bind import bind_memory
from bundles.minimal.runtime import MinimalRuntime
from plugins.patterns.wizard.registry import register as register_wizard

from palm.common.patterns.build_context import PatternBuildContext
from palm.common.patterns.builder import build_pattern
from palm.core import PatternStatus
from palm.core.registry import Registry
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode
from palm.core.transform.registry import transform_registry
from palm.definitions.flow import FlowDefinition
from palm.states.dict_backed_state import DictBackedState


class _TagRule(BaseTransformRule):
    """Prefix the source value with a tag that belongs to this class."""

    name = "tag"
    mode = TransformMode.SINGLE
    tag = "?"

    @classmethod
    def from_options(cls, **options: object) -> _TagRule:
        del options
        return cls()

    def apply(self, context: TransformContext, **options: object) -> TransformContext:
        del options
        return context.advance(self.rule_name, f"{self.tag}:{context.value}")


class _ProcessTag(_TagRule):
    tag = "P"


class _FirstTag(_TagRule):
    tag = "A"


class _SecondTag(_TagRule):
    tag = "B"


def _flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-tag-proof",
        name="tag-proof",
        pattern="wizard",
        options={
            "include_commit": False,
            "steps": [
                {
                    "slug": "mark",
                    "title": "Mark",
                    "step_kind": "transform",
                    "source_key": "name",
                    "target_key": "marked",
                    "rule": "tag",
                },
            ],
        },
    )


def _context(runtime: MinimalRuntime) -> PatternBuildContext:
    return PatternBuildContext(
        event_engine=runtime.event,
        execution=runtime.execution,
        registries=runtime.registries,
    )


def _install_wizard(runtime: MinimalRuntime, rule: type[_TagRule] | None) -> None:
    registries = runtime.registries
    registries.install("pattern", Registry("pattern"))
    registries.install("pattern_builder", Registry("pattern builder"))
    registries.install("wizard_step", Registry("wizard step"))
    if rule is not None:
        table = Registry("transform")
        table.register("tag", rule)
        registries.install("transform", table)
    register_wizard(registries)


def _marked(runtime: MinimalRuntime) -> str:
    pattern = build_pattern(_flow(), context=_context(runtime))
    state = DictBackedState({"name": "ada"})
    status = pattern.tick(state)
    assert status == PatternStatus.SUCCESS
    value = state.get("marked")
    assert isinstance(value, str)
    return value


def test_transform_step_reads_the_system_registry() -> None:
    transform_registry.register("tag", _ProcessTag)
    first = MinimalRuntime()
    second = MinimalRuntime()
    _install_wizard(first, _FirstTag)
    _install_wizard(second, _SecondTag)
    try:
        for runtime in (first, second):
            runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
        assert _marked(first) == "A:ada"
        assert _marked(second) == "B:ada"
        assert transform_registry.get("tag") is _ProcessTag
    finally:
        transform_registry.drop("tag")
        for runtime in (first, second):
            if runtime.is_started:
                runtime.stop()


def test_transform_step_requires_the_transform_registry() -> None:
    runtime = MinimalRuntime()
    _install_wizard(runtime, None)
    runtime.start(drivers=bind_memory(), structure_definition_id="local.embedded")
    try:
        with pytest.raises(RuntimeError, match="transform registry"):
            build_pattern(_flow(), context=_context(runtime))
    finally:
        if runtime.is_started:
            runtime.stop()
