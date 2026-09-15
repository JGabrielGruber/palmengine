"""0.68.14 — unread parking lots and skip stubs composted."""

from __future__ import annotations

import importlib.util

from palm.kits import registry as kits_registry
from palm.system.vitality import (
    CAPABILITY_MONITOR_AGENT,
    default_vitality_registry,
)


def test_system_reexport_shims_are_gone() -> None:
    assert importlib.util.find_spec("palm.system.ports") is None
    assert importlib.util.find_spec("palm.system.planes") is None
    assert importlib.util.find_spec("palm.system.supervisor") is None


def test_utils_and_dag_flow_parking_lots_are_gone() -> None:
    assert importlib.util.find_spec("palm.utils") is None
    assert importlib.util.find_spec("palm.patterns.dag.flow") is None


def test_kits_doctor_section_is_gone() -> None:
    assert not hasattr(kits_registry, "doctor_section")


def test_vitality_skip_stubs_boot_membership_and_log_tail_are_gone() -> None:
    reg = default_vitality_registry()
    assert "boot_membership" not in reg
    assert "system_log_tail" not in reg
    assert CAPABILITY_MONITOR_AGENT in reg
    assert not reg.is_enabled(CAPABILITY_MONITOR_AGENT)
