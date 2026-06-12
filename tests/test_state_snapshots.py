"""Tests for schema-aware state snapshots and resume restoration."""

from __future__ import annotations

from palm.common.executions.flow_submission import (
    prepare_flow_submission,
    prepare_resume_submission,
)
from palm.common.patterns import PatternBuildContext
from palm.common.persistence.state_snapshot import (
    SNAPSHOT_META_KEY,
    snapshot_state,
    state_from_snapshot,
)
from palm.core import SCOPES_ROOT_KEY, DictStateSchema
from palm.definitions import FlowDefinition
from palm.states import BlackboardState
from tests.core.fakes import TestState


def test_snapshot_without_schemas_omits_meta() -> None:
    state = TestState({"plain": True})
    payload = snapshot_state(state)
    assert SNAPSHOT_META_KEY not in payload
    restored = state_from_snapshot(payload)
    assert restored.get("plain") is True
    assert restored.scope_stack() == ()


def test_legacy_snapshot_restores_current_scope_only() -> None:
    state = TestState()
    state.enter_scope("legacy-step")
    state.set_scoped("answer", "yes")
    payload = dict(state.snapshot())
    payload[SNAPSHOT_META_KEY] = {"current_scope": "legacy-step"}

    restored = state_from_snapshot(payload)
    assert restored.scope_stack() == ("legacy-step",)
    assert restored.get_scoped("answer") == "yes"


def test_nested_scope_stack_roundtrip() -> None:
    state = TestState()
    state.enter_scope("wizard")
    state.enter_scope("session")
    state.enter_scope("age")
    state.set_scoped("answer", 30)

    restored = state_from_snapshot(snapshot_state(state))
    assert restored.scope_stack() == ("wizard", "session", "age")
    assert restored.get_scoped("answer") == 30
    assert (
        restored.snapshot()[SCOPES_ROOT_KEY]["wizard"]["__scopes"]["session"]["__scopes"]["age"][
            "answer"
        ]
        == 30
    )


def test_scope_schema_conflict_inner_wins_for_effective_schema() -> None:
    root = DictStateSchema({"type": "string"})
    inner = DictStateSchema({"type": "integer", "minimum": 10})
    state = TestState(schema=root)
    state.bind_scope_schema("inner", inner)
    state.enter_scope("outer")
    assert state.effective_schema() is root
    state.enter_scope("inner")
    assert state.effective_schema() is inner

    meta = snapshot_state(state)[SNAPSHOT_META_KEY]
    assert meta["scope_schemas"]["inner"]["type"] == "integer"
    assert meta["effective_schema"]["type"] == "integer"


def test_resume_prefers_snapshot_schema_over_flow_definition() -> None:
    snapshot_schema = DictStateSchema(
        {
            "type": "object",
            "properties": {"tenant": {"type": "string", "default": "from-snapshot"}},
        },
    )
    state = BlackboardState(schema=snapshot_schema)
    state.set("tenant", "persisted")

    flow = FlowDefinition(
        name="onboard",
        pattern="wizard",
        state_schema={
            "type": "object",
            "properties": {"tenant": {"type": "string", "default": "from-flow"}},
        },
        options={"steps": 1},
    )
    instance_data = {
        "version": 2,
        "kind": "process_instance",
        "instance_id": "inst-1",
        "job_id": "job-1",
        "status": "WAITING_FOR_INPUT",
        "state_snapshot": snapshot_state(state),
        "flow_definition": flow.to_dict(),
        "pattern": "wizard",
        "metadata": {},
    }
    from palm.instances import ProcessInstance

    instance = ProcessInstance.from_dict(instance_data)
    submission = prepare_resume_submission(instance, build_ctx=PatternBuildContext())
    assert submission.state.get("tenant") == "persisted"
    assert submission.state.schema is not None
    assert submission.state.schema.definition["properties"]["tenant"]["default"] == "from-snapshot"


def test_prepare_flow_submission_binds_schema_for_plain_state() -> None:
    flow = FlowDefinition(
        name="plain",
        pattern="wizard",
        state_schema={
            "type": "object",
            "properties": {"region": {"type": "string", "default": "us-east"}},
        },
        options={"steps": 1},
    )
    submission = prepare_flow_submission(
        flow,
        state=None,
        metadata=None,
        instances=None,
        build_ctx=PatternBuildContext(),
    )
    assert submission.state.get("region") == "us-east"
