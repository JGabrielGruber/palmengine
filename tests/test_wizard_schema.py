"""Tests for wizard integration with state schemas."""

from __future__ import annotations

from palm.common.executions.flow_submission import prepare_flow_submission
from palm.common.patterns import PatternBuildContext
from palm.common.persistence.state_snapshot import (
    SNAPSHOT_META_KEY,
    snapshot_state,
    state_from_snapshot,
)
from palm.core import SCOPES_ROOT_KEY, DictStateSchema
from palm.core.behavior_tree import PatternStatus
from palm.core.context import ContextEngine
from palm.definitions import FlowDefinition, StateSchemaDefinition
from palm.patterns.wizard import WizardConfig, WizardKeys, WizardPattern, WizardStepConfig
from palm.states import BlackboardState


def _age_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(
                slug="age",
                title="Age",
                prompt="How old are you?",
                field_type="text",
            ),
        ),
    )


def _age_schema() -> DictStateSchema:
    return DictStateSchema(
        {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 18},
            },
        },
    )


def test_wizard_rejects_schema_invalid_input() -> None:
    state = BlackboardState(schema=_age_schema())
    wizard = WizardPattern(name="onboard", config=_age_config())

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert state.current_scope() == "age"

    wizard.provide_input(state, 16)
    assert wizard.tick(state) == PatternStatus.FAILURE
    assert "minimum" in str(state.get(WizardKeys.VALIDATION_ERROR))
    assert wizard.answers(state) == {}


def test_wizard_accepts_schema_valid_input_and_scopes_answer() -> None:
    state = BlackboardState(schema=_age_schema())
    wizard = WizardPattern(name="onboard", config=_age_config())

    wizard.tick(state)
    wizard.provide_input(state, 25)
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state) == {"age": 25}
    assert state.get("age") == 25
    assert state.current_scope() is None
    assert state.snapshot()[SCOPES_ROOT_KEY]["age"]["answer"] == 25


def test_wizard_step_scope_visible_on_context_engine() -> None:
    ctx = ContextEngine()
    state = BlackboardState(schema=_age_schema())
    ctx.initialize(state=state)
    wizard = WizardPattern(name="onboard", config=_age_config())

    wizard.tick(state)
    assert ctx.current_state_scope == "age"

    wizard.provide_input(state, 30)
    wizard.tick(state)
    assert ctx.current_state_scope is None


def test_flow_inline_schema_preferred_over_reference() -> None:
    from palm.common import DefinitionRepository

    repo = DefinitionRepository()
    repo.register_schema(
        StateSchemaDefinition(
            name="tenant-schema",
            schema={
                "type": "object",
                "properties": {
                    "tenant": {"type": "string", "default": "from-ref"},
                },
            },
        ),
    )
    flow = FlowDefinition(
        name="onboard",
        pattern="wizard",
        state_schema_ref="tenant-schema",
        state_schema={
            "type": "object",
            "properties": {
                "tenant": {"type": "string", "default": "from-inline"},
            },
        },
        options={"steps": 1},
    )
    submission = prepare_flow_submission(
        flow,
        state=None,
        metadata=None,
        instances=None,
        build_ctx=PatternBuildContext(definition_repository=repo),
    )
    assert submission.state.get("tenant") == "from-inline"


def test_snapshot_includes_schema_meta() -> None:
    state = BlackboardState(schema=_age_schema())
    state.enter_scope("age")
    state.set_scoped("answer", 21)

    payload = snapshot_state(state)
    meta = payload[SNAPSHOT_META_KEY]
    assert meta["schema"]["properties"]["age"]["minimum"] == 18
    assert meta["current_scope"] == "age"
    assert meta["scope_depth"] == 1

    restored = state_from_snapshot(payload)
    assert restored.schema is not None
    assert restored.get("age") is None
    assert restored.snapshot()[SCOPES_ROOT_KEY]["age"]["answer"] == 21