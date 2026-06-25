"""Tests for wizard choice resolution — index, name, and partial matching."""

from __future__ import annotations

from palm.common.patterns import PatternBuildContext, build_pattern
from palm.core.behavior_tree import PatternStatus
from palm.definitions import FlowDefinition
from palm.patterns.wizard import WizardPattern
from palm.patterns.wizard.bindings.definitions.config import WizardConfig, WizardStepConfig
from palm.patterns.wizard.flow.validation import (
    choice_selection_error,
    prepare_step_input,
    resolve_choice_value,
)
from palm.states import BlackboardState


def test_resolve_choice_by_index() -> None:
    choices = ("low", "medium", "high")
    assert resolve_choice_value("1", choices) == "low"
    assert resolve_choice_value("2", choices) == "medium"
    assert resolve_choice_value(3, choices) == "high"


def test_resolve_choice_exact_and_case_insensitive() -> None:
    choices = ("developer", "manager")
    assert resolve_choice_value("developer", choices) == "developer"
    assert resolve_choice_value("MANAGER", choices) == "manager"


def test_resolve_choice_partial_unique() -> None:
    choices = ("low", "medium", "high")
    assert resolve_choice_value("med", choices) == "medium"
    assert resolve_choice_value("h", choices) == "high"


def test_resolve_choice_ambiguous_partial_returns_none() -> None:
    choices = ("low", "lower")
    assert resolve_choice_value("lo", choices) is None


def test_resolve_choice_prefers_exact_over_index() -> None:
    choices = ("2", "10", "20")
    assert resolve_choice_value("2", choices) == "2"


def test_choice_selection_error_includes_numbered_list() -> None:
    message = choice_selection_error("nope", ("low", "medium", "high"))
    assert "1. low" in message
    assert "3. high" in message


def test_wizard_step_accepts_numeric_priority() -> None:
    state = BlackboardState()
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="priority",
                title="Priority",
                prompt="How urgent?",
                field_type="choice",
                choices=("low", "medium", "high"),
            ),
        ),
    )
    wizard = WizardPattern(name="w", config=config)
    wizard.tick(state)
    wizard.provide_input(state, "3")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state)["priority"] == "high"


def test_collection_field_accepts_partial_priority() -> None:
    flow = FlowDefinition(
        name="choice-collection",
        pattern="wizard",
        options={
            "include_summary": False,
            "include_commit": False,
            "steps": [
                {
                    "slug": "items",
                    "step_kind": "collection",
                    "title": "Items",
                    "prompt": "Manage items",
                    "collection_key": "items",
                    "min_items": 1,
                    "item_fields": [
                        {
                            "slug": "title",
                            "prompt": "Title?",
                            "state_schema": {"type": "string", "minLength": 1},
                        },
                        {
                            "slug": "priority",
                            "prompt": "Priority?",
                            "field_type": "choice",
                            "choices": ["low", "medium", "high"],
                            "state_schema": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                            },
                        },
                    ],
                },
            ],
        },
    )
    state = BlackboardState()
    built = build_pattern(flow, context=PatternBuildContext())
    assert isinstance(built, WizardPattern)
    wizard = built

    wizard.tick(state)
    wizard.provide_input(state, "Add a new item")
    wizard.tick(state)
    wizard.provide_input(state, "Task")
    wizard.tick(state)
    wizard.provide_input(state, "2")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT

    wizard.provide_input(state, "Continue to summary")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state)["items"] == [{"title": "Task", "priority": "medium"}]


def test_prepare_step_input_rejects_invalid_choice() -> None:
    state = BlackboardState()
    step = WizardStepConfig(
        slug="role",
        title="Role",
        prompt="Role?",
        field_type="choice",
        choices=("developer", "manager"),
    )
    _value, error = prepare_step_input(state, step, "invalid")
    assert error is not None
    assert not error.ok
    assert "1. developer" in error.errors[0]
