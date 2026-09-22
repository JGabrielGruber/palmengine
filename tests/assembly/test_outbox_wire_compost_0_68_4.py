"""0.68.4 — bare enable_event_outbox composted to a DNA-shaped skip."""

from __future__ import annotations

import inspect

from bundles.standard.app.bootstrap import runtime_start_options
from bundles.standard.app.host.boot.host_schedule import build_host_handlers
from bundles.standard.app.settings import PalmSettings
from palm.system.runtime.phase_outbox import run as wire_outbox


def test_settings_and_start_options_drop_the_flag() -> None:
    assert "enable_event_outbox" not in PalmSettings.__dataclass_fields__
    opts = runtime_start_options(PalmSettings.for_tests())
    assert "enable_event_outbox" not in opts
    assert "enable_state_snapshot" in opts


def test_wire_phase_skips_on_dna_omit_not_a_flag() -> None:
    src = inspect.getsource(wire_outbox)
    assert "capability_off:outbox" in src
    assert "enable_event_outbox" not in src
    spawn_src = inspect.getsource(build_host_handlers)
    assert "enable_event_outbox" not in spawn_src
