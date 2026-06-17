"""Tests for interactive WizardPattern."""

from __future__ import annotations

import pytest

from palm.core.behavior_tree import PatternStatus
from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.patterns.wizard import (
    StepValidationRule,
    WizardConfig,
    WizardEventType,
    WizardKeys,
    WizardPattern,
    WizardStepConfig,
)
from palm.patterns.wizard.handler import CommitContext, CommitRegistry, CommitResult
from palm.states import BlackboardState


def _profile_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(
                slug="name",
                title="Your Name",
                prompt="What is your name?",
                field_type="text",
            ),
            WizardStepConfig(
                slug="role",
                title="Your Role",
                prompt="Select a role",
                field_type="choice",
                choices=("developer", "manager", "other"),
            ),
            WizardStepConfig(
                slug="confirm",
                title="Confirm",
                prompt="Save profile?",
                field_type="confirm",
            ),
        ),
        allow_backtrack=True,
    )


def test_wizard_three_step_flow_with_events() -> None:
    events: list[tuple[str, dict]] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda e: events.append((e.type, dict(e.payload))))

    state = BlackboardState()
    wizard = WizardPattern(
        name="onboard",
        config=_profile_config(),
        event_engine=engine,
    )

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "name"
    assert events[-1][0] == WizardEventType.STEP_STARTED

    wizard.provide_input(state, "Ada")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "role"
    event_types = [e[0] for e in events]
    assert WizardEventType.INPUT_RECEIVED in event_types
    assert events[-1][0] == WizardEventType.STEP_STARTED

    wizard.provide_input(state, "developer")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "confirm"

    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert events[-1][0] == WizardEventType.COMPLETED
    assert wizard.answers(state) == {
        "name": "Ada",
        "role": "developer",
        "confirm": "yes",
    }
    assert state.get(WizardKeys.COMPLETED) is True


def test_wizard_rejects_invalid_choice() -> None:
    state = BlackboardState()
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="name",
                title="Name",
                prompt="Name?",
            ),
            WizardStepConfig(
                slug="role",
                title="Role",
                prompt="Role?",
                field_type="choice",
                choices=("a", "b"),
            ),
        ),
    )
    wizard = WizardPattern(name="w", config=config)
    wizard.tick(state)
    wizard.provide_input(state, "Test")
    wizard.tick(state)
    wizard.provide_input(state, "invalid")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "role"


def test_wizard_backtrack_and_reanswer() -> None:
    state = BlackboardState()
    wizard = WizardPattern(name="w", config=_profile_config())

    wizard.tick(state)
    wizard.provide_input(state, "Wrong Name")
    wizard.tick(state)
    wizard.provide_input(state, "developer")
    wizard.tick(state)

    assert wizard.current_step_slug(state) == "confirm"
    wizard.request_backtrack(state, "name")

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "name"

    wizard.provide_input(state, "Correct Name")
    wizard.tick(state)
    wizard.provide_input(state, "manager")
    wizard.tick(state)
    wizard.provide_input(state, True)

    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state)["name"] == "Correct Name"
    assert wizard.answers(state)["role"] == "manager"
    assert wizard.answers(state)["confirm"] is True


def test_wizard_with_context_engine_state_binding() -> None:
    ctx = ContextEngine()
    ctx.initialize()
    state = BlackboardState()
    ctx.push("wizard_session", state=state, session_id="s-1")

    wizard = WizardPattern(
        name="ctx_wizard",
        config=WizardConfig.from_slugs(["alpha", "beta"]),
    )

    assert wizard.tick(ctx.current_state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(ctx.current_state, "first")
    assert wizard.tick(ctx.current_state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(ctx.current_state, "second")
    assert wizard.tick(ctx.current_state) == PatternStatus.SUCCESS

    assert ctx.current_state.get(WizardKeys.COMPLETED) is True
    assert ctx.get("session_id") == "s-1"


def test_wizard_reset_allows_rerun() -> None:
    state = BlackboardState()
    wizard = WizardPattern(
        name="w",
        config=WizardConfig.from_slugs(["only"]),
    )
    wizard.tick(state)
    wizard.provide_input(state, "x")
    assert wizard.tick(state) == PatternStatus.SUCCESS

    wizard.reset()
    state.delete(WizardKeys.COMPLETED)
    state.set(WizardKeys.ANSWERS, {})

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(state, "y")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state)["only"] == "y"


def test_wizard_registry_default_steps() -> None:
    from palm.core import pattern_registry

    cls = pattern_registry.get("wizard")
    state = BlackboardState()
    wizard = cls(name="reg", steps=2)
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(state, "a")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    wizard.provide_input(state, "b")
    assert wizard.tick(state) == PatternStatus.SUCCESS


def test_wizard_pattern_via_behavior_tree_engine() -> None:
    from palm.core import pattern_registry
    from palm.core.behavior_tree import BehaviorTreeEngine

    state = BlackboardState()
    engine = BehaviorTreeEngine()
    engine.initialize(state=state)
    cls = pattern_registry.get("wizard")
    wiz = cls(name="wiz", steps=2)
    engine.set_root(wiz)
    assert engine.tick() == PatternStatus.WAITING_FOR_INPUT
    wiz.provide_input(engine.state, "first")
    assert engine.tick() == PatternStatus.WAITING_FOR_INPUT
    wiz.provide_input(engine.state, "second")
    assert engine.tick() == PatternStatus.SUCCESS
    assert wiz.answers(engine.state)["step_1"] == "first"


def _transactional_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(
                slug="name",
                title="Name",
                prompt="Name?",
                validation=(StepValidationRule("min_length", {"min": 2}),),
            ),
            WizardStepConfig(
                slug="role",
                title="Role",
                prompt="Role?",
                field_type="choice",
                choices=("dev", "mgr"),
            ),
        ),
        allow_backtrack=True,
        include_summary=True,
        include_commit=True,
        commit_hook="save_profile",
    )


def test_transactional_wizard_happy_path_with_commit() -> None:
    from palm.patterns.wizard.handler import CommitRegistry, CommitResult

    registry = CommitRegistry()
    committed: list[dict] = []

    def save_profile(ctx: CommitContext) -> CommitResult:
        committed.append(dict(ctx.answers))
        return CommitResult.success({"stored": True})

    registry.register("save_profile", save_profile)

    state = BlackboardState()
    wizard = WizardPattern(
        name="txn",
        config=_transactional_config(),
        commit_registry=registry,
    )

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "dev")
    wizard.tick(state)
    assert wizard.current_step_slug(state) == "summary"
    wizard.provide_input(state, "yes")
    wizard.tick(state)
    assert wizard.current_step_slug(state) == "commit"
    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.is_committed(state)
    assert committed[0] == {"name": "Ada", "role": "dev"}


def test_validation_min_length_failure() -> None:
    state = BlackboardState()
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="name",
                title="Name",
                prompt="Name?",
                validation=(StepValidationRule("min_length", {"min": 3}),),
            ),
        ),
    )
    wizard = WizardPattern(name="w", config=config)
    wizard.tick(state)
    wizard.provide_input(state, "ab")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert state.get(WizardKeys.VALIDATION_ERROR)
    assert wizard.current_step_slug(state) == "name"


def test_commit_handler_failure() -> None:
    from palm.patterns.wizard.handler import CommitRegistry, CommitResult

    registry = CommitRegistry()

    def failing(_: CommitContext) -> CommitResult:
        return CommitResult.failure("disk full")

    registry.register("save_profile", failing)

    config = WizardConfig(
        steps=(WizardStepConfig(slug="name", title="N", prompt="N?"),),
        include_summary=False,
        include_commit=True,
        commit_hook="save_profile",
    )
    state = BlackboardState()
    wizard = WizardPattern(name="w", config=config, commit_registry=registry)
    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.FAILURE
    assert state.get(WizardKeys.COMMIT_ERROR) == "disk full"


def test_backtrack_blocked_for_commit_step() -> None:
    registry = CommitRegistry()
    registry.register("save_profile", lambda _ctx: CommitResult.success())

    state = BlackboardState()
    wizard = WizardPattern(
        name="w",
        config=_transactional_config(),
        commit_registry=registry,
    )
    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "dev")
    wizard.tick(state)
    wizard.provide_input(state, "yes")
    wizard.tick(state)
    assert wizard.current_step_slug(state) == "commit"
    with pytest.raises(ValueError, match="protected"):
        wizard.request_backtrack(state, "commit")
    with pytest.raises(ValueError, match="protected"):
        wizard.request_backtrack(state, "summary")


def test_legacy_action_step_kind_rejected_by_builder() -> None:
    from palm.common.exceptions import DefinitionBuildError
    from palm.patterns.wizard.builder import wizard_config_from_options

    with pytest.raises(DefinitionBuildError, match="step_kind 'action' was removed"):
        wizard_config_from_options(
            {
                "steps": [
                    {
                        "slug": "lookup",
                        "title": "Lookup",
                        "step_kind": "action",
                        "resource_provider": "rest",
                        "resource_id": "users/1",
                    },
                ],
            },
        )


def test_answers_persist_across_ticks() -> None:
    state = BlackboardState()
    wizard = WizardPattern(name="w", config=_profile_config())

    wizard.tick(state)
    wizard.provide_input(state, "Persist")
    wizard.tick(state)

    assert wizard.answers(state)["name"] == "Persist"
    assert state.get(WizardKeys.ANSWERS)["name"] == "Persist"
