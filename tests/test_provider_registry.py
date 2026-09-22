"""Tests for provider extension registry hooks."""

from __future__ import annotations

import pytest

import plugins.providers  # noqa: F401 — register providers
from palm.common.providers._registry import get_bound_runtime
from plugins.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from bundles.standard.runtimes.embedded import EmbeddedRuntime


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    yield rt
    rt.stop()
    clear_palm_runtime()


def test_runtime_accessor_returns_bound_runtime(runtime: EmbeddedRuntime) -> None:
    assert get_bound_runtime() is runtime
