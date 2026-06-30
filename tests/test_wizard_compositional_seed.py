"""Compositional initial_state seeding into wizard answers."""

from __future__ import annotations

from palm.core.behavior_tree import PatternStatus
from palm.patterns.wizard import WizardConfig, WizardPattern, WizardStepConfig
from palm.patterns.wizard.bindings.compensation.handler import (
    CommitContext,
    CommitRegistry,
    CommitResult,
)
from palm.patterns.wizard.bindings.context.state import (
    get_answers,
    merge_compositional_state_into_answers,
)
from palm.states import BlackboardState


def test_merge_compositional_state_into_answers() -> None:
    state = BlackboardState({"capture_role": "main", "goal": "Compose docs"})
    assert merge_compositional_state_into_answers(state) is True
    assert get_answers(state) == {"capture_role": "main", "goal": "Compose docs"}

    assert merge_compositional_state_into_answers(state) is False


def test_wizard_commit_receives_seeded_capture_role() -> None:
    received: list[dict] = []
    registry = CommitRegistry()

    def capture_commit(ctx: CommitContext) -> CommitResult:
        received.append(dict(ctx.answers))
        role = ctx.answers.get("capture_role")
        node = {"id": "n1", "title": ctx.answers.get("title")}
        if role == "main":
            return CommitResult.success({"node": node, "main_node": node})
        return CommitResult.success({"node": node})

    registry.register("capture", capture_commit)

    state = BlackboardState({"capture_role": "main"})
    wizard = WizardPattern(
        name="capture",
        config=WizardConfig(
            steps=(WizardStepConfig(slug="title", title="Title", prompt="Title?"),),
            include_summary=False,
            include_commit=True,
            commit_hook="capture",
        ),
        commit_registry=registry,
    )

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert get_answers(state).get("capture_role") == "main"

    wizard.provide_input(state, "My Node")
    wizard.tick(state)
    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.SUCCESS

    assert received[0].get("capture_role") == "main"
    assert state.get("__result__") == {
        "node": {"id": "n1", "title": "My Node"},
        "main_node": {"id": "n1", "title": "My Node"},
    }
