"""
Wizard step kind registry — extensible leaf factories for tree construction.

Register custom ``step_kind`` values to extend wizards without editing
``tree.py``. Built-in kinds are registered at import time via
:func:`register_builtin_wizard_step_kinds`.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from palm.core.behavior_tree import BaseNode
from palm.core.context import ContextEngine
from palm.core.exceptions import RegistryError
from palm.core.resource import ResourceEngine
from palm.patterns.wizard.collection_leaf import WizardCollectionLeaf
from palm.patterns.wizard.commit_leaf import WizardCommitLeaf
from palm.patterns.wizard.config import WizardStepConfig
from palm.patterns.wizard.handler import CommitRegistry
from palm.patterns.wizard.resource_leaf import WizardResourceLeaf
from palm.patterns.wizard.step_leaf import EventEmitter, WizardStepLeaf
from palm.patterns.wizard.summary_leaf import WizardSummaryLeaf
from palm.patterns.wizard.transform_leaf import WizardTransformLeaf

WizardStepLeafFactory = Callable[["WizardStepBuildContext"], BaseNode]


@dataclass(frozen=True)
class WizardStepBuildContext:
    """Inputs required to materialize a wizard step leaf."""

    wizard_name: str
    step_index: int
    step: WizardStepConfig
    emit: EventEmitter | None = None
    commit_registry: CommitRegistry | None = None
    resource_engine: ResourceEngine | None = None
    context_engine: ContextEngine | None = None


class WizardStepKindRegistry:
    """Thread-safe registry mapping ``step_kind`` to leaf factories."""

    def __init__(self) -> None:
        self._factories: dict[str, WizardStepLeafFactory] = {}
        self._lock = threading.RLock()

    def register(self, kind: str, factory: WizardStepLeafFactory) -> None:
        if not kind:
            raise ValueError("Wizard step kind must be non-empty")
        with self._lock:
            if self._factories.get(kind) is factory:
                return
            self._factories[kind] = factory

    def has(self, kind: str) -> bool:
        with self._lock:
            return kind in self._factories

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._factories)

    def build(self, ctx: WizardStepBuildContext) -> BaseNode:
        kind = ctx.step.step_kind
        with self._lock:
            factory = self._factories.get(kind)
            if factory is None:
                factory = self._factories.get("input")
            if factory is None:
                available = sorted(self._factories)
                raise RegistryError(
                    f"Unknown wizard step kind {kind!r}. Available: {available}"
                )
        return factory(ctx)

    def clear(self) -> None:
        with self._lock:
            self._factories.clear()


_default_step_registry = WizardStepKindRegistry()


def default_wizard_step_registry() -> WizardStepKindRegistry:
    return _default_step_registry


def _build_interactive_step(ctx: WizardStepBuildContext) -> BaseNode:
    return WizardStepLeaf(
        ctx.step,
        wizard_name=ctx.wizard_name,
        step_index=ctx.step_index,
        emit=ctx.emit,
        context_engine=ctx.context_engine,
    )


def _build_summary_step(ctx: WizardStepBuildContext) -> BaseNode:
    return WizardSummaryLeaf(
        ctx.step,
        wizard_name=ctx.wizard_name,
        step_index=ctx.step_index,
        emit=ctx.emit,
        context_engine=ctx.context_engine,
    )


def _build_commit_step(ctx: WizardStepBuildContext) -> BaseNode:
    hook = ctx.step.commit_hook
    if not hook or ctx.commit_registry is None:
        raise ValueError(
            f"Commit step {ctx.step.slug!r} requires commit_hook and CommitRegistry"
        )
    return WizardCommitLeaf(
        ctx.step,
        wizard_name=ctx.wizard_name,
        step_index=ctx.step_index,
        hook_name=hook,
        commit_registry=ctx.commit_registry,
        resource_engine=ctx.resource_engine,
        emit=ctx.emit,
        context_engine=ctx.context_engine,
    )


def _build_collection_step(ctx: WizardStepBuildContext) -> BaseNode:
    return WizardCollectionLeaf(
        ctx.step,
        wizard_name=ctx.wizard_name,
        step_index=ctx.step_index,
        emit=ctx.emit,
        context_engine=ctx.context_engine,
    )


def _build_resource_step(ctx: WizardStepBuildContext) -> BaseNode:
    return WizardResourceLeaf(
        ctx.step,
        wizard_name=ctx.wizard_name,
        step_index=ctx.step_index,
        resource_engine=ctx.resource_engine,
        emit=ctx.emit,
        context_engine=ctx.context_engine,
    )


def _build_transform_step(ctx: WizardStepBuildContext) -> BaseNode:
    return WizardTransformLeaf(
        ctx.step,
        wizard_name=ctx.wizard_name,
        step_index=ctx.step_index,
        emit=ctx.emit,
        context_engine=ctx.context_engine,
        resource_engine=ctx.resource_engine,
    )


def register_builtin_wizard_step_kinds(
    registry: WizardStepKindRegistry | None = None,
) -> WizardStepKindRegistry:
    """Register Palm built-in wizard step kinds."""
    target = registry or _default_step_registry
    target.register("input", _build_interactive_step)
    target.register("introduction", _build_interactive_step)
    target.register("summary", _build_summary_step)
    target.register("commit", _build_commit_step)
    target.register("collection", _build_collection_step)
    target.register("resource", _build_resource_step)
    target.register("transform", _build_transform_step)
    return target


register_builtin_wizard_step_kinds()