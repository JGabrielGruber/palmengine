"""Tests for definition serialization and repository persistence."""

from __future__ import annotations

import pytest

from palm.common import DefinitionNotFoundError, DefinitionRepository
from palm.common.executions.flow_submission import prepare_flow_submission
from palm.common.patterns import PatternBuildContext
from palm.core import StorageEngine, StorageNotConfiguredError
from palm.definitions import FlowDefinition, ProcessDefinition, StateSchemaDefinition
from palm.states import BlackboardState
from palm.storages import memory  # noqa: F401


def _sample_flow() -> FlowDefinition:
    return FlowDefinition(
        id="flow-onboard-1",
        name="onboard",
        pattern="wizard",
        options={
            "steps": [
                {"slug": "name", "title": "Name", "prompt": "Name?"},
                {"slug": "done", "title": "Done", "prompt": "Done?"},
            ],
        },
    )


def _sample_process() -> ProcessDefinition:
    return ProcessDefinition(
        id="proc-onboard-1",
        name="onboarding",
        flows=[_sample_flow()],
        metadata={"env": "test"},
    )


def test_flow_definition_roundtrip_dict() -> None:
    flow = _sample_flow()
    restored = FlowDefinition.from_dict(flow.to_dict())
    assert restored.definition_id == flow.definition_id
    assert restored.pattern == flow.pattern
    assert restored.options == flow.options


def test_process_definition_roundtrip_dict() -> None:
    process = _sample_process()
    restored = ProcessDefinition.from_dict(process.to_dict())
    assert restored.definition_id == process.definition_id
    assert restored.metadata == process.metadata
    assert len(restored.flows) == 1
    assert restored.flows[0].name == "onboard"


def test_repository_register_without_storage() -> None:
    repo = DefinitionRepository()
    flow = _sample_flow()
    repo.register_flow(flow)
    assert repo.get_flow_by_name("onboard").definition_id == "flow-onboard-1"


def test_repository_save_requires_storage() -> None:
    repo = DefinitionRepository()
    with pytest.raises(StorageNotConfiguredError):
        repo.save_flow(_sample_flow())


def test_repository_flow_persistence_roundtrip() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = DefinitionRepository(storage)
    repo.save_flow(_sample_flow())

    fresh = DefinitionRepository(storage)
    loaded = fresh.get_flow_by_id("flow-onboard-1")
    assert loaded.name == "onboard"
    assert loaded.pattern == "wizard"
    assert len(loaded.options["steps"]) == 2
    storage.shutdown()


def test_repository_process_persistence_roundtrip() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = DefinitionRepository(storage)
    repo.save_process(_sample_process())

    fresh = DefinitionRepository(storage)
    loaded = fresh.get_process_by_name("onboarding")
    assert loaded.definition_id == "proc-onboard-1"
    assert loaded.flows[0].pattern == "wizard"
    storage.shutdown()


def test_repository_delete_flow() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = DefinitionRepository(storage)
    repo.save_flow(_sample_flow())
    assert repo.delete_flow("flow-onboard-1", by_id=True)

    empty = DefinitionRepository(storage)
    with pytest.raises(DefinitionNotFoundError):
        empty.get_flow_by_id("flow-onboard-1")
    storage.shutdown()


def _sample_schema() -> StateSchemaDefinition:
    return StateSchemaDefinition(
        id="schema-user-1",
        name="user",
        schema={
            "type": "object",
            "properties": {
                "tenant": {"type": "string", "default": "acme"},
            },
        },
        metadata={"owner": "platform"},
    )


def test_state_schema_definition_roundtrip_dict() -> None:
    schema = _sample_schema()
    restored = StateSchemaDefinition.from_dict(schema.to_dict())
    assert restored.definition_id == schema.definition_id
    assert restored.schema == schema.schema
    assert restored.metadata == schema.metadata


def test_flow_definition_state_schema_ref_roundtrip() -> None:
    flow = FlowDefinition(
        name="onboard",
        pattern="wizard",
        state_schema_ref="schema-user-1",
        options={"steps": 1},
    )
    restored = FlowDefinition.from_dict(flow.to_dict())
    assert restored.state_schema_ref == "schema-user-1"


def test_repository_schema_persistence_roundtrip() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = DefinitionRepository(storage)
    repo.save_schema(_sample_schema())

    fresh = DefinitionRepository(storage)
    loaded = fresh.get_schema_by_id("schema-user-1")
    assert loaded.name == "user"
    assert loaded.schema["properties"]["tenant"]["default"] == "acme"
    storage.shutdown()


def test_flow_submission_resolves_state_schema_ref() -> None:
    repo = DefinitionRepository()
    repo.register_schema(_sample_schema())
    flow = FlowDefinition(
        name="onboard",
        pattern="wizard",
        state_schema_ref="user",
        options={"steps": 1},
    )
    repo.register_flow(flow)
    submission = prepare_flow_submission(
        flow,
        state=None,
        metadata=None,
        instances=None,
        build_ctx=PatternBuildContext(definition_repository=repo),
    )
    assert isinstance(submission.state, BlackboardState)
    assert submission.state.get("tenant") == "acme"


def test_repository_list_flows() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = DefinitionRepository(storage)
    repo.save_flow(_sample_flow())
    repo.save_flow(
        FlowDefinition(id="flow-2", name="other", pattern="dag"),
    )
    names = {flow.name for flow in repo.list_flows()}
    assert names == {"onboard", "other"}
    storage.shutdown()
