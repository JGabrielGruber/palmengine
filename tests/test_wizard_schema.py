"""Tests for wizard integration with state schemas."""

from __future__ import annotations

from palm.common import DefinitionRepository
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
from palm.patterns.wizard import (
    WizardConfig,
    WizardKeys,
    WizardPattern,
    WizardStepConfig,
    materialize_wizard_step_schemas,
    validate_collected_answers,
)
from palm.patterns.wizard.bindings.compensation.handler import CommitContext, CommitRegistry, CommitResult
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
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert "at least" in str(state.get(WizardKeys.VALIDATION_ERROR)).lower()
    assert wizard.answers(state) == {}
    assert wizard.current_step_slug(state) == "age"


def test_wizard_retries_after_schema_validation_failure() -> None:
    state = BlackboardState(schema=_age_schema())
    wizard = WizardPattern(name="onboard", config=_age_config())

    wizard.tick(state)
    wizard.provide_input(state, 16)
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT

    wizard.provide_input(state, 25)
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state) == {"age": 25}


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


def test_wizard_step_inline_schema_rejects_invalid_input() -> None:
    step_schema = DictStateSchema({"type": "integer", "minimum": 18})
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="age",
                title="Age",
                prompt="How old are you?",
                schema=step_schema,
            ),
        ),
    )
    state = BlackboardState()
    wizard = WizardPattern(name="onboard", config=config)

    wizard.tick(state)
    wizard.provide_input(state, 16)
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert "at least" in str(state.get(WizardKeys.VALIDATION_ERROR)).lower()
    assert wizard.answers(state) == {}


def test_wizard_step_schema_ref_resolved_at_build() -> None:
    repo = DefinitionRepository()
    repo.register_schema(
        StateSchemaDefinition(
            name="email-schema",
            schema={"type": "string", "minLength": 3},
        ),
    )
    config = WizardConfig(
        steps=(
            WizardStepConfig(
                slug="email",
                title="Email",
                prompt="Email?",
                state_schema_ref="email-schema",
            ),
        ),
    )
    built = materialize_wizard_step_schemas(config, repo)
    assert built.steps[0].schema is not None


def test_wizard_summary_validates_full_answers_against_flow_schema() -> None:
    flow_schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "role": {"type": "string", "enum": ["dev", "mgr"]},
                "tenant": {"type": "string"},
            },
            "required": ["name", "role", "tenant"],
        },
    )
    registry = CommitRegistry()
    registry.register("save", lambda _ctx: CommitResult.success())

    config = WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Name?"),
            WizardStepConfig(
                slug="role",
                title="Role",
                prompt="Role?",
                field_type="choice",
                choices=("dev", "mgr"),
            ),
        ),
        include_summary=True,
        include_commit=True,
        commit_hook="save",
    )
    state = BlackboardState(schema=flow_schema)
    wizard = WizardPattern(name="txn", config=config, commit_registry=registry)

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "dev")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "summary"
    assert "Missing required answer: tenant" in str(state.get(WizardKeys.VALIDATION_ERROR))
    errors = state.get(WizardKeys.VALIDATION_ERRORS)
    assert isinstance(errors, list) and errors


def test_validate_collected_answers_reports_missing_required() -> None:
    schema = DictStateSchema(
        {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    )
    state = BlackboardState(schema=schema)
    result = validate_collected_answers(state, {})
    assert not result.ok
    assert "missing required key: name" in result.errors[0]

    from palm.patterns.wizard.flow.validation import format_validation_message

    assert format_validation_message(result.errors[0]) == "Missing required answer: name"


def test_transactional_wizard_commit_revalidates_before_handler() -> None:
    schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "role": {"type": "string", "enum": ["dev"]},
            },
            "required": ["name", "role"],
        },
    )
    registry = CommitRegistry()
    committed: list[dict] = []

    def save(ctx: CommitContext) -> CommitResult:
        committed.append(dict(ctx.answers))
        return CommitResult.success()

    registry.register("save", save)

    config = WizardConfig(
        steps=(
            WizardStepConfig(slug="name", title="Name", prompt="Name?"),
            WizardStepConfig(
                slug="role",
                title="Role",
                prompt="Role?",
                field_type="choice",
                choices=("dev", "mgr"),
            ),
        ),
        include_summary=True,
        include_commit=True,
        commit_hook="save",
    )
    state = BlackboardState(schema=schema)
    wizard = WizardPattern(name="txn", config=config, commit_registry=registry)

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)
    wizard.provide_input(state, "dev")
    wizard.tick(state)
    wizard.provide_input(state, "yes")
    wizard.tick(state)

    answers = dict(wizard.answers(state))
    answers["role"] = "mgr"
    state.set(WizardKeys.ANSWERS, answers)

    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "commit"
    assert not committed
    assert "must be one of" in str(state.get(WizardKeys.VALIDATION_ERROR)).lower()


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
    assert restored.scope_stack() == ("age",)
    assert restored.current_scope() == "age"
    assert restored.get("age") is None
    assert restored.get_scoped("answer") == 21
    assert restored.snapshot()[SCOPES_ROOT_KEY]["age"]["answer"] == 21
