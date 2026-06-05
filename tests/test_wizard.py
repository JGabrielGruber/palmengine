"""Tests for interactive WizardPattern."""

from __future__ import annotations

from palm.core.behavior_tree import PatternStatus
from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.patterns.wizard import (
    WizardConfig,
    WizardEventType,
    WizardKeys,
    WizardPattern,
    WizardStepConfig,
)
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
    assert wizard.tick(state) == PatternStatus.FAILURE


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


def test_answers_persist_across_ticks() -> None:
    state = BlackboardState()
    wizard = WizardPattern(name="w", config=_profile_config())

    wizard.tick(state)
    wizard.provide_input(state, "Persist")
    wizard.tick(state)

    assert wizard.answers(state)["name"] == "Persist"
    assert state.get(WizardKeys.ANSWERS)["name"] == "Persist"