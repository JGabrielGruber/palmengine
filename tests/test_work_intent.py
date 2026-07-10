"""0.37 — pure WorkIntent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from palm.core.work import WorkIntent


def test_work_intent_roundtrip() -> None:
    w = WorkIntent(
        id="w1",
        kind="run_flow",
        target="todo-analytics",
        payload={"reason": "test"},
        coalesce_key="todo-analytics:global",
    )
    w2 = WorkIntent.from_dict(w.to_dict())
    assert w2.target == "todo-analytics"
    assert w2.coalesce_key == "todo-analytics:global"
    assert w2.is_due()


def test_not_before_future() -> None:
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    w = WorkIntent(kind="run_flow", target="x", not_before=future)
    assert w.is_due() is False
