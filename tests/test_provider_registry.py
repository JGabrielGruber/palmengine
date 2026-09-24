"""Tests for provider extension registry hooks."""

from __future__ import annotations

import plugins.providers  # noqa: F401 — register providers
import pytest
from bundles.standard.runtimes.embedded import EmbeddedRuntime
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime

from palm.common.providers._registry import get_bound_runtime


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start(storage_backend="memory")
    yield rt
    rt.stop()
    clear_palm_runtime()


def test_runtime_accessor_returns_bound_runtime(runtime: EmbeddedRuntime) -> None:
    assert get_bound_runtime() is runtime
