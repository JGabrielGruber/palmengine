"""Tests for wizard step kind registry and BT tree construction."""

from __future__ import annotations

import pytest

from palm.common.exceptions import DefinitionBuildError
from palm.core.behavior_tree import ActionNode, BaseNode, PatternStatus, RootNode
from palm.core.context import BaseState
from palm.patterns.wizard.bindings.definitions.builder import wizard_config_from_options
from palm.patterns.wizard.bindings.definitions.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.flow.phases import WizardPhaseContext, WizardSequenceNode
from palm.patterns.wizard.bindings.behavior_tree.backtrack import WizardCompletionGuardNode
from palm.patterns.wizard.flow.extensions.registry import (
    WizardStepKindRegistry,
    default_wizard_step_registry,
    register_builtin_wizard_step_kinds,
)
from palm.patterns.wizard.bindings.behavior_tree.tree import build_wizard_tree
from palm.states import BlackboardState


def test_default_registry_includes_builtin_kinds() -> None:
    names = default_wizard_step_registry().names()
    assert "input" in names
    assert "resource" in names
    assert "collection" in names
    assert "transform" in names


def test_custom_step_kind_can_be_registered() -> None:
    registry = WizardStepKindRegistry()
    register_builtin_wizard_step_kinds(registry)

    def build_note(ctx: WizardPhaseContext) -> BaseNode:
        return ActionNode(
            ctx.step.slug,
            action=lambda _s: PatternStatus.SUCCESS,
        )

    registry.register("note", build_note)
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="note_step",
                title="Note",
                prompt="noop",
                step_kind="note",  # type: ignore[arg-type]
            ),
        ),
    )
    root, sequence = build_wizard_tree("demo", config, step_registry=registry)
    assert isinstance(root.child, WizardCompletionGuardNode)
    assert isinstance(root.child.child, WizardSequenceNode)
    assert len(sequence.children) == 1
    assert sequence.children[0].name == "note_step"


def test_builder_accepts_registered_custom_kind() -> None:
    registry = default_wizard_step_registry()
    registry.register(
        "note",
        lambda ctx: ActionNode(ctx.step.slug, action=lambda _s: PatternStatus.SUCCESS),
    )
    config = wizard_config_from_options(
        {
            "steps": [
                {
                    "slug": "note_step",
                    "title": "Note",
                    "prompt": "noop",
                    "step_kind": "note",
                },
            ],
        },
    )
    assert config.steps[0].step_kind == "note"


def test_builder_rejects_unregistered_custom_kind() -> None:
    with pytest.raises(DefinitionBuildError, match="Invalid wizard step_kind"):
        wizard_config_from_options(
            {
                "steps": [
                    {
                        "slug": "bad",
                        "title": "Bad",
                        "prompt": "?",
                        "step_kind": "not_registered",
                    },
                ],
            },
        )


def test_wizard_tree_wraps_sequence_with_completion_guard() -> None:
    config = WizardConfig.from_slugs(["alpha"])
    root, sequence = build_wizard_tree("demo", config)
    assert isinstance(root, RootNode)
    assert isinstance(root.child, WizardCompletionGuardNode)
    assert root.child.child is sequence
    assert isinstance(sequence, WizardSequenceNode)


def test_wizard_sequence_jump_to_index(test_state: BaseState) -> None:
    config = WizardConfig.from_slugs(["a", "b", "c"])
    _root, sequence = build_wizard_tree("demo", config)
    sequence.jump_to_index(2)
    assert sequence.current_index == 2
    sequence.restore_position(test_state, 1)
    assert sequence.current_index == 1
    assert test_state.get("__wizard__.current_step") == "b"


@pytest.fixture
def test_state() -> BlackboardState:
    return BlackboardState()