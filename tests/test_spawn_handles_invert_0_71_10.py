"""0.71.10 — invert RegisteredPlaceSpawn.handles off the mixed bag.

Place-id body stash lives on typed register_body / body / forget_body.
os: process registry is typed os_registry. No handles dict. No __os_registry__.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from palm.system.structure import (
    PlaceSpawnResult,
    RegisteredPlaceSpawn,
    combined_structure_spawn_port,
    os_prefix_spawn_port,
)
from palm.system.structure.place_spawn import OsProcessRegistry

_STRUCTURE = Path(__file__).resolve().parents[1] / "src" / "palm" / "system" / "structure"


def test_registered_spawn_has_no_handles_field() -> None:
    names = {f.name for f in fields(RegisteredPlaceSpawn)}
    assert "handles" not in names
    port = RegisteredPlaceSpawn()
    assert not hasattr(port, "handles")


def test_ensure_ready_registers_typed_body() -> None:
    port = RegisteredPlaceSpawn()

    def ensure_yard(place_id: str, payload: dict) -> PlaceSpawnResult:
        return PlaceSpawnResult(state="ready", reason="registered", handle="yard-1")

    port.register("work_yard", ensure=ensure_yard)
    result = port.ensure("work_yard")
    assert result.state == "ready"
    assert port.body("work_yard") == "yard-1"


def test_release_forgets_typed_body() -> None:
    port = RegisteredPlaceSpawn()

    def ensure_yard(place_id: str, payload: dict) -> PlaceSpawnResult:
        return PlaceSpawnResult(state="ready", reason="registered", handle="yard-1")

    def release_yard(place_id: str) -> PlaceSpawnResult:
        return PlaceSpawnResult(state="gone", reason="released")

    port.register("work_yard", ensure=ensure_yard, release=release_yard)
    port.ensure("work_yard")
    assert port.body("work_yard") == "yard-1"
    port.release("work_yard")
    assert port.body("work_yard") is None


def test_os_prefix_exposes_typed_os_registry() -> None:
    reg = OsProcessRegistry()
    port = os_prefix_spawn_port(registry=reg)
    assert port.os_registry is reg
    assert "__os_registry__" not in getattr(port, "bodies", {})


def test_combined_copies_typed_os_registry() -> None:
    reg = OsProcessRegistry()
    port = combined_structure_spawn_port(os_registry=reg)
    assert port.os_registry is reg
    assert not hasattr(port, "handles")


def test_structure_sources_have_no_handles_bag_or_os_magic_key() -> None:
    for name in ("place_spawn.py", "workload_place.py"):
        text = (_STRUCTURE / name).read_text(encoding="utf-8")
        assert 'handles["__os_registry__"]' not in text, f"{name} still stashes __os_registry__"
        assert 'handles.get("__os_registry__")' not in text, f"{name} still reads __os_registry__"
        assert "__os_registry__" not in text, f"{name} still names magic os key"
        assert "self.handles" not in text, f"{name} still uses handles bag"
        assert "port.handles" not in text, f"{name} still uses handles bag"
        assert "combined.handles" not in text, f"{name} still uses handles bag"
