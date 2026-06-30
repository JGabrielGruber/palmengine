"""Tests for snapshot diff helper."""

from __future__ import annotations

from palm.common.operator.snapshots import diff_snapshot_states


def test_diff_snapshot_states_detects_changes() -> None:
    diff = diff_snapshot_states(
        {"state_snapshot": {"name": "Ada", "__bt_x": 1}},
        {"state_snapshot": {"name": "Bob", "email": "bob@example.com"}},
    )
    assert diff["added_keys"] == ["email"]
    assert diff["removed_keys"] == []
    assert diff["changed"][0]["key"] == "name"
    assert diff["change_count"] == 2
