"""0.68.7 — write-only RunnerApp bag composted. Autoload + core registry stay."""

from __future__ import annotations

import importlib.util

import plugins.runners  # noqa: F401
from palm.core.workload.registry import workload_runtime_registry
from plugins.runners._apps import INSTALLED_RUNNERS


def test_runner_app_bag_is_gone() -> None:
    assert importlib.util.find_spec("plugins.runners.app") is None
    assert importlib.util.find_spec("plugins.runners._registry") is None
    for name in INSTALLED_RUNNERS:
        assert importlib.util.find_spec(f"plugins.runners.{name}.app") is None


def test_autoload_still_registers_workload_runtimes() -> None:
    assert INSTALLED_RUNNERS == ("local", "host", "neonroot")
    names = set(workload_runtime_registry.names())
    for name in INSTALLED_RUNNERS:
        assert name in names
