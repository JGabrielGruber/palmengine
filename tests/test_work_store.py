"""0.37 — WorkIntentStore coalesce + claim."""

from __future__ import annotations

from palm.common.work import WorkIntentStore
from palm.core.storage import StorageEngine
from palm.core.work import WorkIntent


def _storage() -> StorageEngine:
    s = StorageEngine()
    s.initialize()
    s.select("memory")
    return s


def test_enqueue_claim_ack() -> None:
    store = WorkIntentStore(_storage())
    store.enqueue(WorkIntent(kind="run_flow", target="a"))
    assert store.pending_count() == 1
    claimed = store.claim_due(limit=5)
    assert len(claimed) == 1
    store.ack(claimed[0].id)
    assert store.pending_count() == 0


def test_coalesce_replaces_pending() -> None:
    store = WorkIntentStore(_storage())
    store.enqueue(
        WorkIntent(id="1", kind="run_flow", target="a", coalesce_key="k")
    )
    store.enqueue(
        WorkIntent(id="2", kind="run_flow", target="a", coalesce_key="k")
    )
    pending = store.list_pending()
    assert len(pending) == 1
    assert pending[0].id == "2"
