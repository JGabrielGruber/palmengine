"""Human-readable number formatting for CLI present (Linux -h spirit).

Used by vitality benchmark (and any other operate tables). Does not change
system/JSON truth — only display strings for humans.
"""

from __future__ import annotations

from typing import Any


def human_bytes(n: float | int | None, *, from_unit: str = "B") -> str:
    """Format a size with binary units (KiB, MiB, …).

    *from_unit*: ``B`` (bytes), ``KB`` / ``KiB`` (treat as kibibytes input).
    """
    if n is None:
        return "—"
    try:
        value = float(n)
    except (TypeError, ValueError):
        return str(n)
    if value < 0:
        return f"-{human_bytes(-value, from_unit=from_unit)}"
    scale = str(from_unit or "B").upper()
    if scale in {"KB", "KIB"}:
        value *= 1024.0
    elif scale in {"MB", "MIB"}:
        value *= 1024.0 ** 2
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(value)} {units[idx]}"
    if value >= 100:
        return f"{value:.0f} {units[idx]}"
    if value >= 10:
        return f"{value:.1f} {units[idx]}"
    return f"{value:.2f} {units[idx]}"


def human_duration_s(seconds: float | int | None) -> str:
    """Format a duration given in seconds."""
    if seconds is None:
        return "—"
    try:
        s = float(seconds)
    except (TypeError, ValueError):
        return str(seconds)
    if s < 0:
        return f"-{human_duration_s(-s)}"
    if s == 0:
        return "0 s"
    if s < 1e-3:
        return f"{s * 1e6:.0f} µs"
    if s < 1.0:
        return f"{s * 1e3:.2f} ms"
    if s < 60.0:
        return f"{s:.3f} s" if s < 10 else f"{s:.2f} s"
    minutes, rem = divmod(s, 60.0)
    if minutes < 60:
        return f"{int(minutes)}m {rem:.1f}s"
    hours, minutes = divmod(minutes, 60.0)
    return f"{int(hours)}h {int(minutes)}m"


def human_duration_ms(ms: float | int | None) -> str:
    if ms is None:
        return "—"
    try:
        return human_duration_s(float(ms) / 1000.0)
    except (TypeError, ValueError):
        return str(ms)


def human_count(n: float | int | None) -> str:
    """Integer-ish counts with thin grouping (1_234 → 1,234)."""
    if n is None:
        return "—"
    try:
        if isinstance(n, float) and not n.is_integer():
            if abs(n) < 0.001:
                return f"{n:.3g}"
            return f"{n:,.3f}".rstrip("0").rstrip(".")
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def human_delta(value: float | int | None, *, metric: str = "") -> str:
    """Signed delta with metric-aware unit."""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "+" if v > 0 else ""
    body = human_metric_value(v if v >= 0 else -v, metric=metric)
    if v < 0:
        return f"-{body}"
    if v == 0:
        return body
    return f"{sign}{body}"


def human_metric_value(value: Any, *, metric: str = "") -> str:
    """Pick a unit from *metric* key name (rss_kb, cpu_user_s, …)."""
    if value is None:
        return "—"
    key = str(metric or "").lower()
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    if key.endswith("_kb") or key in {"rss_kb", "peak_rss_kb", "primary_rss_kb"}:
        return human_bytes(num, from_unit="KB")
    if key.endswith("_ms") or key in {"recipe_ms", "total_ms"}:
        return human_duration_ms(num)
    if key.endswith("_s") or "cpu_" in key:
        return human_duration_s(num)
    if key.endswith("_lines") or "lines" in key:
        return human_count(int(num)) if float(num).is_integer() else human_count(num)
    if isinstance(value, float) and not float(value).is_integer():
        # tiny cpu-like leftovers
        if abs(num) < 1.0 and ("cpu" in key or key.endswith("_s")):
            return human_duration_s(num)
        return human_count(num)
    return human_count(num)


__all__ = [
    "human_bytes",
    "human_count",
    "human_delta",
    "human_duration_ms",
    "human_duration_s",
    "human_metric_value",
]
