"""Tests for wizard step routing via step params (0.23.1)."""

from __future__ import annotations

from palm.patterns.wizard.bindings.behavior_tree.tree import build_wizard_tree
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.definitions.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.flow.phases._base import provide_wizard_input
from palm.states import BlackboardState


def _config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(
                slug="intent",
                title="Intent",
                prompt="Choose",
                field_type="choice",
                choices=("a", "b"),
                params={"route_on_answer": {"b": "alt", "default": "summary"}},
            ),
            WizardStepConfig(slug="alt", title="Alt", prompt="Alt path"),
            WizardStepConfig(
                slug="summary",
                title="Summary",
                prompt="Confirm",
                field_type="confirm",
                step_kind="summary",
            ),
        ),
        include_summary=False,
    )


def test_route_on_answer_jumps_past_skipped_step() -> None:
    state = BlackboardState()
    root, _sequence = build_wizard_tree("demo", _config())
    assert root.tick(state).name == "WAITING_FOR_INPUT"
    provide_wizard_input(state, "a")
    assert root.tick(state).name == "WAITING_FOR_INPUT"
    assert state.get(WizardKeys.CURRENT_STEP) == "summary"


def test_complete_on_finishes_without_remaining_steps() -> None:
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="catalog",
                title="Catalog",
                prompt="Exit when done",
                params={"complete_on": ["exit"]},
            ),
        ),
        include_summary=False,
    )
    state = BlackboardState()
    root, _sequence = build_wizard_tree("demo", config)
    assert root.tick(state).name == "WAITING_FOR_INPUT"
    provide_wizard_input(state, "exit")
    assert root.tick(state).name == "SUCCESS"
    assert state.get(WizardKeys.COMPLETED) is True