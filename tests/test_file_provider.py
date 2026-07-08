"""Tests for the file document resource provider."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.common import DefinitionRepository
from palm.common.resource import resource_definition_resolver
from palm.core.resource import ResourceEngine
from palm.definitions import ResourceDefinition
from palm.providers.file.provider import FileProvider
from palm.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


@pytest.fixture(autouse=True)
def _clear_bound_runtime() -> None:
    clear_palm_runtime()


def test_file_provider_read_write_delete(tmp_path) -> None:
    provider = FileProvider(name="file")
    root = tmp_path / "documents"
    write = provider.invoke(
        "write",
        resource_id="profiles/alice.json",
        params={
            "documents_root": str(root),
            "format": "json",
            "content": {"visit_count": 1},
        },
    )
    assert write.success is True
    assert write.data["bytes"] > 0

    read = provider.invoke(
        "read",
        resource_id="profiles/alice.json",
        params={"documents_root": str(root), "format": "json"},
    )
    assert read.success is True
    assert read.data["content"]["visit_count"] == 1

    exists = provider.invoke(
        "exists",
        resource_id="profiles/alice.json",
        params={"documents_root": str(root)},
    )
    assert exists.success is True
    assert exists.data["exists"] is True

    deleted = provider.invoke(
        "delete",
        resource_id="profiles/alice.json",
        params={"documents_root": str(root)},
    )
    assert deleted.success is True
    assert deleted.data["deleted"] is True

    missing = provider.invoke(
        "read",
        resource_id="profiles/alice.json",
        params={"documents_root": str(root)},
    )
    assert missing.success is False


def test_file_provider_list_glob(tmp_path) -> None:
    provider = FileProvider(name="file")
    root = tmp_path / "documents"
    provider.invoke(
        "write",
        resource_id="coconut/players/alice.json",
        params={"documents_root": str(root), "content": {"a": 1}},
    )
    provider.invoke(
        "write",
        resource_id="coconut/players/bob.json",
        params={"documents_root": str(root), "content": {"b": 2}},
    )
    result = provider.invoke(
        "list",
        params={"documents_root": str(root), "glob": "coconut/**/*.json"},
    )
    assert result.success is True
    assert result.data["paths"] == [
        "coconut/players/alice.json",
        "coconut/players/bob.json",
    ]


def test_file_provider_resolves_documents_root_from_runtime(tmp_path) -> None:
    runtime = EmbeddedRuntime()
    runtime.start()
    runtime.storage.select("filesystem", data_dir=tmp_path)
    bind_palm_runtime(runtime)
    try:
        provider = FileProvider(name="file")
        write = provider.invoke(
            "write",
            resource_id="profiles/alice.json",
            params={"content": {"visit_count": 3}},
        )
        assert write.success is True
        expected_root = tmp_path / "documents"
        assert write.data["documents_root"] == str(expected_root.resolve())
        assert (expected_root / "profiles" / "alice.json").exists()
    finally:
        runtime.stop()
        clear_palm_runtime()


def test_resource_engine_invoke_file_with_state_binding(tmp_path) -> None:
    engine = ResourceEngine()
    engine.initialize()
    root = tmp_path / "documents"
    result = engine.invoke(
        provider="file",
        action="write",
        resource_id="players/{{ state.player_name }}.json",
        params={
            "documents_root": str(root),
            "value": {"reputation": "friend"},
        },
        state=BlackboardState({"player_name": "Ada"}),
    )
    assert result.success is True

    loaded = engine.invoke(
        provider="file",
        action="read",
        resource_id="players/{{ state.player_name }}.json",
        params={"documents_root": str(root)},
        state=BlackboardState({"player_name": "Ada"}),
    )
    assert loaded.success is True
    assert loaded.data["content"]["reputation"] == "friend"
    engine.shutdown()


def test_resource_engine_invoke_via_definition_ref(tmp_path) -> None:
    root = tmp_path / "documents"
    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            id="resource-read-profile",
            name="read-profile",
            provider="file",
            action="read",
            resource_id="profiles/{{ state.player_name }}.json",
            params={"documents_root": str(root), "format": "json"},
        )
    )
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(repo))
    seed = engine.invoke(
        provider="file",
        action="write",
        resource_id="profiles/{{ state.player_name }}.json",
        params={
            "documents_root": str(root),
            "value": {"visit_count": 2},
        },
        state=BlackboardState({"player_name": "Bob"}),
    )
    assert seed.success is True

    loaded = engine.invoke(
        "read-profile",
        state=BlackboardState({"player_name": "Bob"}),
    )
    assert loaded.success is True
    assert loaded.data["content"]["visit_count"] == 2
    engine.shutdown()


def test_file_provider_describe_lists_actions() -> None:
    provider = FileProvider(name="file")
    descriptor = provider.describe()
    action_names = {action.name for action in descriptor.actions}
    assert action_names == {"read", "write", "delete", "exists", "list"}