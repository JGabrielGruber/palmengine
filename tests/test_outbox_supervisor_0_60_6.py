"""0.60.6 / 0.65.2 — outbox is a DNA-listed supervised service."""

from __future__ import annotations

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.supervisor import OutboxLoopService
from tests.helpers.bound import bound_for_runtime


def test_embedded_store_does_not_register_outbox() -> None:
    """Embedded DNA omits outbox — store skip and loop omit are the same listing."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.outbox_processor is None
        assert rt.supervisor is not None
        assert "outbox" not in rt.supervisor.names()
        assert "work_drain" not in rt.supervisor.names()
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.outbox.wire"].outcome == "skip"
        assert by_id["system.outbox.wire"].reason == "capability_off:outbox"
        assert by_id["system.background.start"].outcome == "skip"
        assert by_id["system.background.start"].reason == "none_registered"
    finally:
        rt.stop()


def test_cli_dna_starts_outbox_when_store_wired() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.background.start"].outcome == "ok"
        assert rt.supervisor is not None
        assert "outbox" in rt.supervisor.status()["running"]
        svc = rt.supervisor.get("outbox")
        assert isinstance(svc, OutboxLoopService)
        assert svc.is_running is True
    finally:
        rt.stop()


def test_outbox_and_work_drain_both_start() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        assert rt.supervisor is not None
        running = set(rt.supervisor.status()["running"])
        assert running == {"outbox", "work_drain"}
    finally:
        rt.stop()
