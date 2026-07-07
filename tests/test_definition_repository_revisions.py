"""Tests for append-only flow definition revisions (0.24.1)."""

from __future__ import annotations

import pytest

from palm.common import DefinitionNotFoundError, DefinitionRepository
from palm.core import StorageEngine, StorageNotConfiguredError
from palm.definitions import FlowDefinition
from palm.storages import memory  # noqa: F401


def _sample_flow(*, name: str = "onboard", options: dict | None = None) -> FlowDefinition:
    return FlowDefinition(
        id="flow-onboard-1",
        name=name,
        pattern="wizard",
        options=options
        or {
            "steps": [
                {"slug": "name", "title": "Name", "prompt": "Name?"},
            ],
        },
    )


def test_publish_flow_revision_starts_at_one() -> None:
    repo = DefinitionRepository()
    published = repo.publish_flow_revision(_sample_flow())
    assert published.revision == 1
    assert repo.get_latest_revision("flow-onboard-1") == 1


def test_publish_flow_revision_increments() -> None:
    repo = DefinitionRepository()
    repo.publish_flow_revision(_sample_flow())
    second = repo.publish_flow_revision(
        _sample_flow(
            options={
                "steps": [
                    {"slug": "done", "title": "Done", "prompt": "Done?"},
                ],
            },
        ),
    )
    assert second.revision == 2
    assert repo.get_latest_revision("flow-onboard-1") == 2


def test_get_flow_by_id_resolves_latest() -> None:
    repo = DefinitionRepository()
    repo.publish_flow_revision(_sample_flow())
    repo.publish_flow_revision(
        _sample_flow(options={"steps": [{"slug": "v2", "title": "V2", "prompt": "?"}]}),
    )
    latest = repo.get_flow_by_id("flow-onboard-1")
    assert latest.revision == 2
    assert latest.options["steps"][0]["slug"] == "v2"


def test_get_flow_by_id_loads_explicit_revision() -> None:
    repo = DefinitionRepository()
    repo.publish_flow_revision(_sample_flow())
    repo.publish_flow_revision(
        _sample_flow(options={"steps": [{"slug": "v2", "title": "V2", "prompt": "?"}]}),
    )
    first = repo.get_flow_by_id("flow-onboard-1", revision=1)
    assert first.revision == 1
    assert first.options["steps"][0]["slug"] == "name"


def test_list_flow_revisions_returns_index() -> None:
    repo = DefinitionRepository()
    repo.publish_flow_revision(_sample_flow())
    repo.publish_flow_revision(_sample_flow())
    rows = repo.list_flow_revisions("flow-onboard-1")
    assert [row["revision"] for row in rows] == [1, 2]


def test_register_flow_delegates_to_publish() -> None:
    repo = DefinitionRepository()
    first = repo.register_flow(_sample_flow())
    second = repo.register_flow(
        _sample_flow(options={"steps": [{"slug": "b", "title": "B", "prompt": "?"}]}),
    )
    assert first.revision == 1
    assert second.revision == 2


def test_legacy_storage_record_loads_as_revision_one() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    storage.set(
        "palm:definitions:flow:flow-onboard-1",
        _sample_flow().to_dict(),
    )
    storage.set("palm:definitions:index:flow", ["flow-onboard-1"])

    repo = DefinitionRepository(storage)
    loaded = repo.get_flow_by_id("flow-onboard-1")
    assert loaded.revision == 1
    assert repo.get_latest_revision("flow-onboard-1") == 1
    storage.shutdown()


def test_save_flow_persists_revisions() -> None:
    storage = StorageEngine()
    storage.initialize(backend="memory")
    repo = DefinitionRepository(storage)
    repo.save_flow(_sample_flow())
    repo.save_flow(
        _sample_flow(options={"steps": [{"slug": "v2", "title": "V2", "prompt": "?"}]}),
    )

    fresh = DefinitionRepository(storage)
    assert fresh.get_latest_revision("flow-onboard-1") == 2
    assert fresh.get_flow_by_id("flow-onboard-1", revision=1).options["steps"][0]["slug"] == "name"
    storage.shutdown()


def test_delete_flow_removes_all_revisions() -> None:
    repo = DefinitionRepository()
    repo.publish_flow_revision(_sample_flow())
    repo.publish_flow_revision(_sample_flow())
    assert repo.delete_flow("flow-onboard-1", by_id=True) is True
    with pytest.raises(DefinitionNotFoundError):
        repo.get_flow_by_id("flow-onboard-1")


def test_get_unknown_revision_raises() -> None:
    repo = DefinitionRepository()
    repo.publish_flow_revision(_sample_flow())
    with pytest.raises(DefinitionNotFoundError):
        repo.get_flow_by_id("flow-onboard-1", revision=99)


def test_save_flow_requires_storage() -> None:
    repo = DefinitionRepository()
    with pytest.raises(StorageNotConfiguredError):
        repo.save_flow(_sample_flow())