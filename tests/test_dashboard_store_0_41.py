"""0.41.0 — durable dashboard registry on StorageEngine."""

from __future__ import annotations

from palm.core.storage import StorageEngine
from palm.definitions.dashboard import DashboardDefinition, DashboardTile
from palm.services.analytics.dashboard_store import DashboardStore
from palm.services.analytics.dashboards import (
    attach_dashboard_store,
    clear_dashboards,
    get_dashboard,
    list_dashboards,
    register_dashboard,
)


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_dashboard_store_roundtrip() -> None:
    storage = _storage()
    store = DashboardStore(storage)
    dash = DashboardDefinition(
        name="ops-test",
        title="Ops",
        tiles=[DashboardTile(id="t1", dataset="palm-todos", profile="table")],
    )
    store.save(dash)
    loaded = store.get("ops-test")
    assert loaded is not None
    assert loaded.name == "ops-test"
    assert len(loaded.tiles) == 1
    assert "ops-test" in store.list_names()


def test_attach_survives_clear_memory() -> None:
    storage = _storage()
    clear_dashboards()
    attach_dashboard_store(storage)
    register_dashboard(
        DashboardDefinition(
            name="persist-me",
            tiles=[DashboardTile(id="a", dataset="x", profile="table")],
        ),
        persist=True,
    )
    clear_dashboards()  # memory only — store still holds def
    # get_dashboard rehydrates from store (0.41)
    assert get_dashboard("persist-me") is not None
    clear_dashboards()
    n = attach_dashboard_store(storage)
    assert n >= 1
    assert any(d["name"] == "persist-me" for d in list_dashboards())
    clear_dashboards()
