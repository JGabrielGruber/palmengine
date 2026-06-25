"""Tests for layered wizard schemas and scope-visible prompts."""

from __future__ import annotations

from palm.common.persistence.state_snapshot import snapshot_state, state_from_snapshot
from palm.core.behavior_tree import PatternStatus
from palm.core.context import ContextEngine
from palm.patterns.wizard import WizardConfig, WizardKeys, WizardPattern, WizardStepConfig
from palm.states import BlackboardState


def _layered_config() -> WizardConfig:
    return WizardConfig(
        steps=(
            WizardStepConfig(
                slug="name",
                title="Name",
                prompt="Name?",
                state_schema={"type": "string"},
                validation=(),
            ),
            WizardStepConfig(
                slug="age",
                title="Age",
                prompt="Age?",
                state_schema={"type": "integer", "minimum": 18},
            ),
            WizardStepConfig(
                slug="role",
                title="Role",
                prompt="Role?",
                field_type="choice",
                choices=("dev", "mgr"),
                state_schema={"type": "string", "enum": ["dev", "mgr"]},
            ),
        ),
        include_summary=True,
        include_commit=False,
    )


def test_layered_schemas_coerce_cli_string_input_for_integer_steps() -> None:
    from palm.core import DictStateSchema
    from palm.patterns.wizard.bindings.definitions.builder import materialize_wizard_step_schemas

    flow_schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 18},
                "role": {"type": "string", "enum": ["dev", "mgr"]},
            },
            "required": ["name", "age", "role"],
        },
    )
    config = materialize_wizard_step_schemas(_layered_config())
    state = BlackboardState(schema=flow_schema)
    wizard = WizardPattern(name="layered", config=config)

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)

    wizard.provide_input(state, "27")
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert wizard.current_step_slug(state) == "role"
    assert wizard.answers(state)["age"] == 27


def test_layered_schemas_validate_step_and_flow_levels() -> None:
    from palm.core import DictStateSchema

    flow_schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 18},
                "role": {"type": "string", "enum": ["dev", "mgr"]},
            },
            "required": ["name", "age", "role"],
        },
    )
    from palm.patterns.wizard.bindings.definitions.builder import materialize_wizard_step_schemas

    config = materialize_wizard_step_schemas(_layered_config())
    state = BlackboardState(schema=flow_schema)
    wizard = WizardPattern(name="layered", config=config)

    wizard.tick(state)
    assert state.scope_schemas().get("name") is not None
    wizard.provide_input(state, "Ada")
    wizard.tick(state)

    wizard.provide_input(state, 16)
    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert "at least" in str(state.get(WizardKeys.VALIDATION_ERROR)).lower()

    wizard.provide_input(state, 25)
    wizard.tick(state)
    wizard.provide_input(state, "dev")
    wizard.tick(state)
    wizard.provide_input(state, "yes")
    assert wizard.tick(state) == PatternStatus.SUCCESS
    assert wizard.answers(state) == {"name": "Ada", "age": 25, "role": "dev"}


def test_active_prompt_includes_scope_context() -> None:
    ctx = ContextEngine()
    state = BlackboardState()
    ctx.initialize(state=state)
    wizard = WizardPattern(
        name="scoped",
        config=WizardConfig.from_slugs(["alpha", "beta"]),
        context_engine=ctx,
    )

    wizard.tick(state)
    prompt = state.get(WizardKeys.ACTIVE_PROMPT)
    assert isinstance(prompt, dict)
    assert prompt["scope_stack"] == ["alpha"]
    assert prompt["current_scope"] == "alpha"
    assert prompt["scope_depth"] == 1


def test_wizard_resume_restores_scope_and_step_schema() -> None:
    from palm.core import DictStateSchema
    from palm.definitions import FlowDefinition
    from palm.instances import ProcessInstance
    from palm.patterns.wizard.bindings.definitions.builder import materialize_wizard_step_schemas

    config = materialize_wizard_step_schemas(_layered_config())
    flow_schema = DictStateSchema(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 18},
                "role": {"type": "string", "enum": ["dev", "mgr"]},
            },
            "required": ["name", "age", "role"],
        },
    )
    state = BlackboardState(schema=flow_schema)
    wizard = WizardPattern(name="resume", config=config)

    wizard.tick(state)
    wizard.provide_input(state, "Ada")
    wizard.tick(state)

    instance = ProcessInstance(
        instance_id="inst-layered",
        job_id="job-layered",
        status="WAITING_FOR_INPUT",
        state_snapshot=snapshot_state(state),
        flow_definition=FlowDefinition(
            name="resume",
            pattern="wizard",
            options={"steps": []},
        ).to_dict(),
        pattern="wizard",
        current_step_slug="age",
    )
    restored_state = state_from_snapshot(instance.state_snapshot)
    assert restored_state.scope_stack() == ("age",)
    assert restored_state.scope_schemas().get("age") is not None

    assert restored_state.get(WizardKeys.ANSWERS) == {"name": "Ada"}
    assert restored_state.effective_schema().definition["minimum"] == 18
