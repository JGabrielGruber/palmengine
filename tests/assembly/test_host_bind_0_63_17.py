"""0.63.17 — host auto-bind WorkloadEngine into default assembly seat."""

from __future__ import annotations

from palm.core.structure import StructureDefinition, StructurePhase, local_embedded
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure import (
    PlaceEffectPort,
    RecordingEffectPort,
    StructureEffectPort,
    StructureSeat,
    WorkloadPlaceSpawn,
    bind_host_structure_to_seat,
    default_structure_effects,
    place_effect_port,
    resolve_workload_engine,
    workload_spawn_hands,
)


def test_resolve_workload_engine_uninitialized() -> None:
    from palm.core.workload import WorkloadEngine

    class _Shell:
        workload = WorkloadEngine()

    assert resolve_workload_engine(_Shell()) is None


def test_default_structure_effects_has_structure_prefixes() -> None:
    hands = default_structure_effects(engine=None)
    assert isinstance(hands, StructureEffectPort)
    spawn = hands.spawn
    assert "workload:" in spawn.prefix_ensures
    assert "os:" in spawn.prefix_ensures
    # Bare place still falls through in-process.
    result = spawn.ensure("local_yard")
    assert result.state == "ready"
    assert result.reason == "in_process"
    # workload unbound fails closed
    wl = spawn.ensure("workload:x")
    assert wl.state == "failed"
    assert wl.reason == "workload_engine_not_bound"


def test_bind_upgrades_in_process_and_attaches_engine() -> None:
    from palm.core.workload import WorkloadEngine
    from plugins.runners.local.runtime import LocalWorkloadRuntime

    eng = WorkloadEngine()
    eng.initialize(
        default_runtime="local",
        runtimes={"local": LocalWorkloadRuntime(name="local")},
    )
    try:

        class _Shell:
            workload = eng

        seat = StructureSeat()  # default StructureEffectPort / in-process
        report = bind_host_structure_to_seat(seat, _Shell(), bind_workload=True)
        assert report["bound"] is True
        assert report["engine"] is True
        assert report["spawn"] == "combined"
        hands = workload_spawn_hands(place_effect_port(seat.effects).spawn)  # type: ignore[union-attr]
        assert isinstance(hands, WorkloadPlaceSpawn)
        assert hands.engine is eng

        dna = StructureDefinition(
            id="local.with_workload_place",
            places_required=("workload:manor",),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is True
        assert seat.admission().phase is StructurePhase.READY
    finally:
        eng.shutdown()


def test_bind_disabled_leaves_workload_fail_closed() -> None:
    from palm.core.workload import WorkloadEngine
    from plugins.runners.local.runtime import LocalWorkloadRuntime

    eng = WorkloadEngine()
    eng.initialize(
        default_runtime="local",
        runtimes={"local": LocalWorkloadRuntime(name="local")},
    )
    try:

        class _Shell:
            workload = eng

        seat = StructureSeat()
        report = bind_host_structure_to_seat(seat, _Shell(), bind_workload=False)
        assert report["bound"] is True
        assert report["engine"] is False
        assert report["skipped"] == "bind_disabled"
        dna = StructureDefinition(
            id="local.needs_wl",
            places_required=("workload:x",),
        )
        seat.assemble(dna)
        assert seat.admission().may_run_business is False
    finally:
        eng.shutdown()


def test_bind_skips_recording_effect_port() -> None:
    from palm.core.workload import WorkloadEngine

    eng = WorkloadEngine()
    eng.initialize()
    try:

        class _Shell:
            workload = eng

        seat = StructureSeat(effects=RecordingEffectPort(auto_ack_places=True))
        report = bind_host_structure_to_seat(seat, _Shell())
        assert report["skipped"] == "no_place_effects"
        assert report["bound"] is False
    finally:
        eng.shutdown()


def test_bind_idempotent_already_bound() -> None:
    from palm.core.workload import WorkloadEngine
    from plugins.runners.local.runtime import LocalWorkloadRuntime

    eng = WorkloadEngine()
    eng.initialize(
        default_runtime="local",
        runtimes={"local": LocalWorkloadRuntime(name="local")},
    )
    try:

        class _Shell:
            workload = eng

        seat = StructureSeat(effects=default_structure_effects(engine=eng))
        report = bind_host_structure_to_seat(seat, _Shell())
        assert report["spawn"] == "already"
        assert report["engine"] is True
    finally:
        eng.shutdown()


def test_runtime_start_binds_workload_engine() -> None:
    """system.engines.init then assemble — default seat holds live engine."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.structure is not None
        assert isinstance(rt.structure.effects, StructureEffectPort)
        port = place_effect_port(rt.structure.effects)
        assert port is not None
        hands = workload_spawn_hands(port.spawn)
        assert hands is not None
        assert hands.engine is rt.workload
        assert rt.workload.is_initialized
        # Bare DNA still admits (no workload places required).
        assert rt.admission.may_run_business is True
        assert rt.admission.definition_id == local_embedded().id
    finally:
        rt.stop()


def test_runtime_bind_workload_false() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        storage_backend="memory",
        structure_bind_workload=False,
    )
    try:
        assert rt.structure is not None
        port = place_effect_port(rt.structure.effects)
        assert port is not None
        hands = workload_spawn_hands(port.spawn)
        assert hands is not None
        assert hands.engine is None
        # Explicit DNA with workload place fails closed when bind off.
        rt.structure.assemble(
            StructureDefinition(
                id="local.wl",
                places_required=("workload:blocked",),
            )
        )
        assert rt.structure.admission().may_run_business is False
    finally:
        rt.stop()


def test_runtime_workload_place_converges_on_host_path() -> None:
    """End-to-end: host seat + DNA requiring workload: place → ready."""
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory")
    try:
        assert rt.admission.may_run_business is True
        dna = StructureDefinition(
            id="local.host_workload_place",
            places_required=("workload:support",),
        )
        loop = rt.structure.assemble(dna)  # type: ignore[union-attr]
        assert loop.steady is True
        assert rt.structure.admission().may_run_business is True  # type: ignore[union-attr]
        assert rt.structure.admission().phase is StructurePhase.READY  # type: ignore[union-attr]
        port = place_effect_port(rt.structure.effects)  # type: ignore[union-attr]
        assert port is not None
        assert "workload:support" in port.registry.places
    finally:
        rt.stop()


def test_place_effect_port_helper() -> None:
    bare = PlaceEffectPort()
    assert place_effect_port(bare) is bare
    port = StructureEffectPort()
    assert place_effect_port(port) is port.places
    assert place_effect_port(RecordingEffectPort()) is None
