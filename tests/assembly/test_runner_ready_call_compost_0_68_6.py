"""0.68.6 — runner ready() call composted. Pattern/Provider ready stays.

0.68.7 dropped the RunnerApp postcard, so register() cannot call ready().
"""

from __future__ import annotations

import importlib.util
import inspect

from palm.common.patterns.app import PatternApp
from palm.common.providers.app import ProviderApp
from plugins.runners.host import registry as host_registry
from plugins.runners.local import registry as local_registry
from plugins.runners.neonroot import registry as neonroot_registry


def test_runner_register_does_not_call_ready() -> None:
    assert importlib.util.find_spec("plugins.runners.app") is None
    for mod in (local_registry, host_registry, neonroot_registry):
        src = inspect.getsource(mod)
        assert "ready" not in src


def test_pattern_and_provider_ready_stay() -> None:
    assert callable(PatternApp.ready)
    assert callable(ProviderApp.ready)
    assert "self.ready()" in inspect.getsource(PatternApp.register)
    assert "self.ready()" in inspect.getsource(ProviderApp.register)
