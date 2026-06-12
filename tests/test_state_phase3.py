"""Tests for Phase 3 state schema, snapshot resume, and observability."""

from __future__ import annotations

from palm.common.persistence.instance_sync import build_instance_from_job, update_instance_from_job
from palm.common.persistence.state_snapshot import SNAPSHOT_META_KEY, snapshot_state, state_from_snapshot
from palm.common.state import (
    STATE_SCOPE_ENTERED,
    STATE_VALUE_SET,
    observe_state,
)
from palm.core import DictStateSchema
from palm.core.behavior_tree import PatternStatus
from palm.core.context import ContextEngine
from palm.core.event import EventEngine
from palm.core.orchestration import Job, JobStatus
from palm.definitions import FlowDefinition
from palm.patterns.wizard import WizardConfig, WizardKeys, WizardPattern, WizardStepConfig
from palm.states import BlackboardState
from tests.core.fakes import TestState


def test_snapshot_includes_scope_stack_and_scope_schemas() -> None:
    flow_schema = DictStateSchema(
        {"type": "object", "properties": {"name": {"type": "string"}}},
    )
    step_schema = DictStateSchema({"type": "integer", "minimum": 18})
    state = BlackboardState(schema=flow_schema)
    state.bind_scope_schema("age", step_schema)
    state.enter_scope("session")
    state.enter_scope("age")
    state.set_scoped("answer", 21)

    meta = snapshot_state(state)[SNAPSHOT_META_KEY]
    assert meta["scope_stack"] == ["session", "age"]
    assert meta["current_scope"] == "age"
    assert "age" in meta["scope_schemas"]
    assert meta["scope_schemas"]["age"]["minimum"] == 18
    assert meta["effective_schema"]["minimum"] == 18


def test_state_from_snapshot_restores_scope_stack_and_schemas() -> None:
    flow_schema = DictStateSchema(
        {"type": "object", "properties": {"name": {"type": "string"}}},
    )
    step_schema = DictStateSchema({"type": "integer", "minimum": 18})
    state = BlackboardState(schema=flow_schema)
    state.bind_scope_schema("age", step_schema)
    state.enter_scope("age")
    state.set_scoped("answer", 25)

    restored = state_from_snapshot(snapshot_state(state))
    assert restored.scope_stack() == ("age",)
    assert restored.current_scope() == "age"
    assert restored.effective_schema() is not None
    assert restored.effective_schema().definition["minimum"] == 18
    assert restored.get_scoped("answer") == 25


def test_effective_schema_prefers_inner_scope() -> None:
    root = DictStateSchema({"type": "string"})
    inner = DictStateSchema({"type": "integer"})
    state = TestState(schema=root)
    state.bind_scope_schema("inner", inner)
    state.enter_scope("outer")
    assert state.effective_schema() is root
    state.enter_scope("inner")
    assert state.effective_schema() is inner


def test_context_engine_exposes_scope_stack_and_effective_schema() -> None:
    schema = DictStateSchema({"type": "integer", "minimum": 1})
    state = TestState()
    ctx = ContextEngine()
    ctx.initialize(state=state)
    ctx.bind_scope_schema("step", schema)
    ctx.enter_state_scope("step")

    assert ctx.state_scope_stack == ("step",)
    assert ctx.effective_schema is schema


def test_observe_state_emits_scope_events_by_default() -> None:
    events: list[tuple[str, dict]] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda event: events.append((event.type, dict(event.payload))))

    state = TestState()
    observe_state(state, engine, source="test")
    state.enter_scope("job")
    state.set_scoped("token", "abc")

    types = [item[0] for item in events]
    assert STATE_SCOPE_ENTERED in types
    assert STATE_VALUE_SET not in types
    entered = next(payload for kind, payload in events if kind == STATE_SCOPE_ENTERED)
    assert entered["scope"] == "job"
    assert entered["scope_stack"] == ["job"]


def test_instance_record_includes_state_meta() -> None:
    schema = DictStateSchema(
        {"type": "object", "properties": {"tenant": {"type": "string"}}},
    )
    state = BlackboardState(schema=schema)
    state.enter_scope("wizard")
    flow = FlowDefinition(name="onboard", pattern="wizard", options={"steps": 1})
    job = Job(
        id="job-1",
        executable=object(),
        state=state,
        metadata={"pattern": "wizard"},
        status=JobStatus.WAITING_FOR_INPUT,
    )
    instance = build_instance_from_job(job, flow=flow, instance_id="inst-1")
    assert instance.state_meta["scope_stack"] == ["wizard"]
    assert instance.state_meta["schema"]["properties"]["tenant"]["type"] == "string"

    state.enter_scope("step_1")
    update_instance_from_job(instance, job)
    assert instance.state_meta["scope_stack"] == ["wizard", "step_1"]


def test_wizard_with_context_engine_syncs_scope_stack() -> None:
    ctx = ContextEngine()
    state = BlackboardState()
    ctx.initialize(state=state)

    wizard = WizardPattern(
        name="ctx_wizard",
        config=WizardConfig.from_slugs(["alpha"]),
        context_engine=ctx,
    )

    assert wizard.tick(state) == PatternStatus.WAITING_FOR_INPUT
    assert ctx.state_scope_stack == ("alpha",)
    assert state.scope_stack() == ("alpha",)