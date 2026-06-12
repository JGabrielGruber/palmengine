"""Tests for wizard collection steps — repeatable items with scoped fields."""

from __future__ import annotations

from palm.common.patterns import PatternBuildContext, build_pattern
from palm.core.behavior_tree import PatternStatus
from palm.definitions import FlowDefinition
from palm.patterns.wizard import WizardKeys, WizardPattern
from palm.patterns.wizard.handler import CommitContext, CommitResult, default_commit_registry
from palm.patterns.wizard.keys import WizardKeys as Keys
from palm.states import BlackboardState


def _todo_flow() -> FlowDefinition:
    return FlowDefinition(
        name="todo-test",
        pattern="wizard",
        state_schema={
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "minLength": 1},
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                            },
                        },
                        "required": ["title", "priority"],
                    },
                },
            },
            "required": ["todos"],
        },
        options={
            "include_summary": True,
            "include_commit": True,
            "commit_hook": "test_persist_todos",
            "steps": [
                {
                    "slug": "todos",
                    "step_kind": "collection",
                    "title": "Todos",
                    "prompt": "Manage todos",
                    "collection_key": "todos",
                    "min_items": 2,
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


def _build() -> WizardPattern:
    default_commit_registry().register(
        "test_persist_todos",
        lambda ctx: CommitResult.success({"todos": ctx.answers.get("todos")}),
    )
    built = build_pattern(_todo_flow(), context=PatternBuildContext())
    assert isinstance(built, WizardPattern)
    return built


def _menu_input(wizard: WizardPattern, state: BlackboardState, choice: str) -> None:
    wizard.provide_input(state, choice)
    wizard.tick(state)


def test_collection_add_two_items_and_complete() -> None:
    state = BlackboardState(schema=_todo_flow().materialize_state_schema())
    wizard = _build()

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "todos"

    _menu_input(wizard, state, "Add a new item")
    wizard.provide_input(state, "Buy milk")
    wizard.tick(state)
    wizard.provide_input(state, "high")
    wizard.tick(state)

    _menu_input(wizard, state, "Add a new item")
    wizard.provide_input(state, "Walk dog")
    wizard.tick(state)
    wizard.provide_input(state, "medium")
    wizard.tick(state)

    _menu_input(wizard, state, "Continue to summary")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "summary"

    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "commit"

    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state)["todos"] == [
        {"title": "Buy milk", "priority": "high"},
        {"title": "Walk dog", "priority": "medium"},
    ]


def test_collection_edit_and_remove() -> None:
    state = BlackboardState(schema=_todo_flow().materialize_state_schema())
    wizard = _build()

    wizard.tick(state)
    _menu_input(wizard, state, "Add a new item")
    wizard.provide_input(state, "First")
    wizard.tick(state)
    wizard.provide_input(state, "low")
    wizard.tick(state)

    _menu_input(wizard, state, "Edit #1: First [low]")
    wizard.provide_input(state, "Updated")
    wizard.tick(state)
    wizard.provide_input(state, "high")
    wizard.tick(state)

    items = state.get(WizardKeys.ANSWERS, {}).get("todos", [])
    assert items[0]["title"] == "Updated"
    assert items[0]["priority"] == "high"


def test_collection_optional_field_accepts_empty_input() -> None:
    flow = FlowDefinition(
        name="todo-optional-date",
        pattern="wizard",
        state_schema={
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "minLength": 1},
                            "due_date": {"type": "string"},
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                            },
                        },
                        "required": ["title", "priority"],
                    },
                },
            },
            "required": ["todos"],
        },
        options={
            "include_summary": False,
            "include_commit": False,
            "steps": [
                {
                    "slug": "todos",
                    "step_kind": "collection",
                    "title": "Todos",
                    "prompt": "Manage todos",
                    "collection_key": "todos",
                    "min_items": 1,
                    "item_fields": [
                        {
                            "slug": "title",
                            "prompt": "Title?",
                            "state_schema": {"type": "string", "minLength": 1},
                        },
                        {
                            "slug": "due_date",
                            "prompt": "Due date?",
                            "required": False,
                            "state_schema": {"type": ["string", "null"]},
                            "validation": [
                                {
                                    "rule": "regex",
                                    "params": {
                                        "pattern": r"^$|^\d{4}-\d{2}-\d{2}$",
                                        "message": "Use YYYY-MM-DD or leave empty",
                                    },
                                }
                            ],
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
    state = BlackboardState(schema=flow.materialize_state_schema())
    built = build_pattern(flow, context=PatternBuildContext())
    assert isinstance(built, WizardPattern)
    wizard = built

    wizard.tick(state)
    _menu_input(wizard, state, "Add a new item")
    wizard.provide_input(state, "Walk dog")
    wizard.tick(state)
    wizard.provide_input(state, "")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(state, "medium")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT

    _menu_input(wizard, state, "Continue to summary")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state)["todos"] == [
        {"title": "Walk dog", "priority": "medium"},
    ]


def test_collection_resume_preserves_list_and_phase() -> None:
    from palm.common.persistence.state_snapshot import snapshot_state, state_from_snapshot

    state = BlackboardState(schema=_todo_flow().materialize_state_schema())
    wizard = _build()
    wizard.tick(state)
    _menu_input(wizard, state, "Add a new item")
    wizard.provide_input(state, "Resume me")
    wizard.tick(state)

    restored = state_from_snapshot(snapshot_state(state))
    wizard2 = _build()
    wizard2.tick(restored)

    assert restored.get(Keys.COLLECTION_PHASE) == "field"
    assert restored.get(Keys.COLLECTION_DRAFT) == {"title": "Resume me"}
    assert wizard2.current_step_slug(restored) == "todos"