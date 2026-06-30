"""Tests for provider extension registry hooks."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers
from palm.providers._registry import get_bound_runtime
from palm.providers.palm.bindings.runtimes.wiring import clear_palm_runtime
from palm.runtimes.embedded import EmbeddedRuntime


@pytest.fixture
def runtime() -> EmbeddedRuntime:
    rt = EmbeddedRuntime()
    rt.start()
    yield rt
    rt.stop()
    clear_palm_runtime()


def test_runtime_accessor_returns_bound_runtime(runtime: EmbeddedRuntime) -> None:
    assert get_bound_runtime() is runtime
