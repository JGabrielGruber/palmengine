"""Shared fast PalmSettings builders for tests outside pytest fixtures."""

from __future__ import annotations

from pathlib import Path

from palm.app.settings import PalmSettings


def make_test_settings(
    *,
    load_examples: bool = False,
    full_recovery: bool = False,
    storage_backend: str = "memory",
    data_dir: Path | None = None,
) -> PalmSettings:
    """Build merged test settings for explicit bootstrap calls."""
    settings = PalmSettings.for_tests(
        load_examples=load_examples,
        full_recovery=full_recovery,
    )
    updates: dict[str, object] = {"storage_backend": storage_backend}
    if data_dir is not None:
        updates["data_dir"] = data_dir
    return settings.model_copy(update=updates)