"""CLI human-readable unit helpers (Linux -h spirit)."""

from __future__ import annotations

from bundles.standard.runtimes.cli.shared.humanize import (
    human_bytes,
    human_count,
    human_delta,
    human_duration_ms,
    human_duration_s,
    human_metric_value,
)


def test_human_bytes_from_kb() -> None:
    assert human_bytes(1024, from_unit="KB") == "1.00 MiB"
    assert "KiB" in human_bytes(500, from_unit="KB")
    assert human_bytes(None) == "—"


def test_human_duration() -> None:
    assert "ms" in human_duration_s(0.002)
    assert "µs" in human_duration_s(0.000_001) or "us" in human_duration_s(0.000_001).lower() or "µs" in human_duration_s(1e-6)
    assert human_duration_ms(2.5).endswith("ms") or "ms" in human_duration_ms(2.5)


def test_human_metric_rss_and_cpu() -> None:
    assert "MiB" in human_metric_value(49564, metric="rss_kb") or "KiB" in human_metric_value(
        49564, metric="rss_kb"
    )
    assert "ms" in human_metric_value(0.0012, metric="cpu_user_s")
    assert human_delta(20, metric="emission_count").startswith("+")
    assert human_count(1234) == "1,234"
