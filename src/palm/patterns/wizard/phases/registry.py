"""
Wizard step kind registry — maps step kinds to phase builders.
"""

from __future__ import annotations

import threading
from collections.abc import Callable

from palm.core.behavior_tree import BaseNode
from palm.core.exceptions import RegistryError
from palm.patterns.wizard.phases._base import EventEmitter, WizardPhaseContext
from palm.patterns.wizard.phases.collection.step import build_collection_phase
from palm.patterns.wizard.phases.commit import build_commit_phase
from palm.patterns.wizard.phases.input import build_input_phase
from palm.patterns.wizard.phases.resource import build_resource_phase
from palm.patterns.wizard.phases.summary import build_summary_phase
from palm.patterns.wizard.phases.transform import build_transform_phase

WizardStepLeafFactory = Callable[[WizardPhaseContext], BaseNode]

# Backward name used by tests and builder metadata.
WizardStepBuildContext = WizardPhaseContext


class WizardStepKindRegistry:
    """Thread-safe registry mapping ``step_kind`` to phase node factories."""

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

    def build(self, ctx: WizardPhaseContext) -> BaseNode:
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


def _build_commit(ctx: WizardPhaseContext) -> BaseNode:
    hook = ctx.step.commit_hook
    return build_commit_phase(ctx, hook_name=hook)


def register_builtin_wizard_step_kinds(
    registry: WizardStepKindRegistry | None = None,
) -> WizardStepKindRegistry:
    target = registry or _default_step_registry
    target.register("input", build_input_phase)
    target.register("introduction", build_input_phase)
    target.register("summary", build_summary_phase)
    target.register("commit", _build_commit)
    target.register("collection", build_collection_phase)
    target.register("resource", build_resource_phase)
    target.register("transform", build_transform_phase)
    return target


register_builtin_wizard_step_kinds()