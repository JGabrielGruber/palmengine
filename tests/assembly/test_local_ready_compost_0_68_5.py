"""0.68.5 — LocalRunnerApp empty ready() override composted.

0.68.7 dropped the RunnerApp bag, so the override cannot return.
"""

from __future__ import annotations

import importlib.util


def test_local_has_no_ready_override() -> None:
    assert importlib.util.find_spec("plugins.runners.local.app") is None
    assert importlib.util.find_spec("plugins.runners.host.app") is None
    assert importlib.util.find_spec("plugins.runners.neonroot.app") is None
