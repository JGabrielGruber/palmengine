"""Tests for the KV resource provider."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.common import DefinitionRepository
from palm.common.resource import resource_definition_resolver
from palm.common.resource.document_storage import clear_memory_kv_store
from palm.core.resource import ResourceEngine
from palm.definitions import ResourceDefinition
from palm.providers.kv.provider import KvProvider
from palm.providers.palm.bindings.runtimes.wiring import bind_palm_runtime, clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime
from palm.states import BlackboardState


@pytest.fixture(autouse=True)
def _clear_kv_memory() -> None:
    clear_memory_kv_store()
    clear_palm_runtime()


def test_kv_provider_get_put_delete_memory() -> None:
    provider = KvProvider(name="kv")
    provider.connect()
    put = provider.invoke(
        "put",
        resource_id="players/alice",
        params={"namespace": "coconut", "backend": "memory", "value": {"visit_count": 1}},
    )
    assert put.success is True

    got = provider.invoke(
        "get",
        resource_id="players/alice",
        params={"namespace": "coconut", "backend": "memory", "default": {}},
    )
    assert got.success is True
    assert got.data["found"] is True
    assert got.data["value"]["visit_count"] == 1

    deleted = provider.invoke(
        "delete",
        resource_id="players/alice",
        params={"namespace": "coconut", "backend": "memory"},
    )
    assert deleted.success is True
    assert deleted.data["deleted"] is True

    missing = provider.invoke(
        "get",
        resource_id="players/alice",
        params={"namespace": "coconut", "backend": "memory", "default": {"empty": True}},
    )
    assert missing.success is True
    assert missing.data["found"] is False
    assert missing.data["value"] == {"empty": True}


def test_kv_provider_list_memory() -> None:
    provider = KvProvider(name="kv")
    provider.invoke(
        "put",
        resource_id="players/alice",
        params={"namespace": "coconut", "backend": "memory", "value": {"a": 1}},
    )
    provider.invoke(
        "put",
        resource_id="players/bob",
        params={"namespace": "coconut", "backend": "memory", "value": {"b": 2}},
    )
    result = provider.invoke(
        "list",
        params={"namespace": "coconut", "backend": "memory", "prefix": "players"},
    )
    assert result.success is True
    assert result.data["keys"] == ["alice", "bob"]


def test_kv_provider_auto_uses_storage_when_runtime_filesystem(tmp_path) -> None:
    runtime = EmbeddedRuntime()
    runtime.start()
    runtime.storage.select("filesystem", data_dir=tmp_path)
    bind_palm_runtime(runtime)
    try:
        provider = KvProvider(name="kv")
        put = provider.invoke(
            "put",
            resource_id="players/alice",
            params={"namespace": "coconut", "backend": "auto", "value": {"visit_count": 3}},
        )
        assert put.success is True
        assert put.data["backend"] == "storage"

        got = provider.invoke(
            "get",
            resource_id="players/alice",
            params={"namespace": "coconut", "backend": "auto"},
        )
        assert got.success is True
        assert got.data["found"] is True
        assert got.data["value"]["visit_count"] == 3
    finally:
        runtime.stop()
        clear_palm_runtime()


def test_resource_engine_invoke_kv_with_state_binding() -> None:
    engine = ResourceEngine()
    engine.initialize()
    result = engine.invoke(
        provider="kv",
        action="put",
        resource_id="players/{{ state.player_name }}",
        params={
            "namespace": "coconut",
            "backend": "memory",
            "value": {"reputation": "friend"},
        },
        state=BlackboardState({"player_name": "Ada"}),
    )
    assert result.success is True

    loaded = engine.invoke(
        provider="kv",
        action="get",
        resource_id="players/{{ state.player_name }}",
        params={"namespace": "coconut", "backend": "memory", "default": {}},
        state=BlackboardState({"player_name": "Ada"}),
    )
    assert loaded.success is True
    assert loaded.data["value"]["reputation"] == "friend"
    engine.shutdown()


def test_resource_engine_invoke_via_definition_ref() -> None:
    repo = DefinitionRepository()
    repo.register_resource(
        ResourceDefinition(
            id="resource-load-coconut-player",
            name="load-coconut-player",
            provider="kv",
            action="get",
            resource_id="players/{{ state.player_name }}",
            params={"namespace": "coconut", "backend": "memory", "default": {}},
        )
    )
    engine = ResourceEngine()
    engine.initialize(definition_resolver=resource_definition_resolver(repo))
    seed = engine.invoke(
        provider="kv",
        action="put",
        resource_id="players/{{ state.player_name }}",
        params={
            "namespace": "coconut",
            "backend": "memory",
            "value": {"visit_count": 2},
        },
        state=BlackboardState({"player_name": "Bob"}),
    )
    assert seed.success is True

    loaded = engine.invoke(
        "load-coconut-player",
        state=BlackboardState({"player_name": "Bob"}),
    )
    assert loaded.success is True
    assert loaded.data["found"] is True
    assert loaded.data["value"]["visit_count"] == 2
    engine.shutdown()


def test_kv_provider_describe_lists_actions() -> None:
    provider = KvProvider(name="kv")
    descriptor = provider.describe()
    action_names = {action.name for action in descriptor.actions}
    assert action_names == {"get", "put", "delete", "list"}