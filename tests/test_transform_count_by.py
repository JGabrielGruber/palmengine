"""count_by transform rule — definition-only rollups."""

from __future__ import annotations

from palm.common.transforms.rules.count_by import CountByRule
from palm.core.transform.base import TransformContext


def test_count_by_priority() -> None:
    rows = [
        {"title": "a", "priority": "high"},
        {"title": "b", "priority": "low"},
        {"title": "c", "priority": "high"},
    ]
    ctx = TransformContext(original=rows)
    out = CountByRule(field="priority").apply(ctx)
    assert out.value == [
        {"priority": "high", "count": 2},
        {"priority": "low", "count": 1},
    ]
