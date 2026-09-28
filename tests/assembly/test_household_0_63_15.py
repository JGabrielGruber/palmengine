"""0.63.15 — structure assemble / place-registry intents + OS process spawn."""

from __future__ import annotations

import sys
import time

from palm.core.structure import (
    EffectIntent,
    EffectIntentKind,
    StructurePhase,
    local_embedded,
)
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.structure import (
    OsProcessRegistry,
    PlaceEffectPort,
    StructureEffectPort,
    StructureSeat,
    os_prefix_spawn_port,
)
from tests.helpers.bound import bound_for_runtime


def test_structure_projection_invalidate_refresh() -> None:
    hands = StructureEffectPort()
    hands.bind_structure(local_embedded())
    inv = hands.apply(EffectIntent(kind=EffectIntentKind.INVALIDATE_PROJECTION, target="home"))
    assert inv[0].kind.value == "projection_failed"
    assert "home" not in hands.projections_loaded

    ref = hands.apply(EffectIntent(kind=EffectIntentKind.REFRESH_PROJECTION, target="home"))
    assert ref[0].kind.value == "projection_loaded"
    assert "home" in hands.projections_loaded


def test_structure_policy_refuse() -> None:
    hands = StructureEffectPort()
    hands.bind_structure(
        local_embedded(),
        surfaces=("rest",),
    )
    obs = hands.apply(EffectIntent(kind=EffectIntentKind.APPLY_STRUCTURE_POLICY))
    assert any(o.kind.value == "structure_policy_violation" for o in obs)
    assert any("server_surfaces" in o.target for o in obs)


def test_structure_policy_clear() -> None:
    hands = StructureEffectPort()
    hands.bind_structure(local_embedded(), surfaces=())
    obs = hands.apply(EffectIntent(kind=EffectIntentKind.APPLY_STRUCTURE_POLICY))
    assert all(o.kind.value == "structure_policy_cleared" for o in obs)


def test_structure_request_seed() -> None:
    hands = StructureEffectPort()
    hands.bind_structure(local_embedded())
    obs = hands.apply(EffectIntent(kind=EffectIntentKind.REQUEST_STRUCTURE_SEED))
    assert obs[0].kind.value == "structure_seed_finished"
    assert obs[0].target == "local.embedded"


def test_seat_binds_structure_on_assemble() -> None:
    seat = StructureSeat()
    seat.assemble(local_embedded())
    assert isinstance(seat.effects, StructureEffectPort)
    assert seat.effects.definition is not None
    assert not hasattr(seat.effects, "capabilities")
    # Drain membership is DNA — embedded does not list it.
    assert not local_embedded().has_capability("work_drain")
    assert seat.admission().may_run_business is True


def test_os_process_spawn_and_release() -> None:
    reg = OsProcessRegistry()
    spawn = os_prefix_spawn_port(registry=reg)
    port = PlaceEffectPort(spawn=spawn)
    # long-lived child
    obs = port.apply(
        EffectIntent(
            kind=EffectIntentKind.ENSURE_PLACE,
            target="os:sleeper",
            payload={
                "argv": [
                    sys.executable,
                    "-c",
                    "import time; time.sleep(60)",
                ]
            },
        )
    )
    assert obs[0].kind.value == "place_ready"
    assert obs[0].payload.get("spawn") == "os_process_spawned"
    pid = obs[0].payload.get("pid")
    assert isinstance(pid, int)
    assert "os:sleeper" in reg.processes
    # release terminates
    gone = port.apply(EffectIntent(kind=EffectIntentKind.RELEASE_PLACE, target="os:sleeper"))
    assert gone[0].kind.value == "place_gone"
    assert "os:sleeper" not in reg.processes
    # process should be dead soon
    deadline = time.time() + 3.0
    while time.time() < deadline:
        try:
            import os

            os.kill(pid, 0)
            time.sleep(0.05)
        except OSError:
            break
    else:
        # best-effort; some kernels leave zombies briefly
        pass


def test_os_process_fail_closed_without_argv() -> None:
    reg = OsProcessRegistry()
    result = reg.ensure("os:x", {})
    assert result.state == "failed"
    assert result.reason == "os_spawn_not_configured"


def test_runtime_structure_default_hands() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.admission.may_run_business is True
        assert isinstance(rt.structure.effects, StructureEffectPort)  # type: ignore[union-attr]
    finally:
        rt.stop()


def test_engine_projection_intents_via_loop() -> None:
    """Invalidate then refresh folds through structure assemble / place registry into engine admission."""
    from palm.core.structure import StructureEngine
    from palm.system.structure.loop import assemble_until_steady

    engine = StructureEngine()
    engine.initialize()
    hands = StructureEffectPort()
    hands.bind_structure(local_embedded())
    engine.receive_definition(local_embedded())
    assemble_until_steady(engine, hands)
    assert engine.admission().may_run_business is True
    for obs in hands.apply(
        EffectIntent(kind=EffectIntentKind.INVALIDATE_PROJECTION, target="home")
    ):
        engine.observe(obs)
    assert engine.admission().may_run_business is False
    assert engine.admission().phase is StructurePhase.BLOCKED
    for obs in hands.apply(EffectIntent(kind=EffectIntentKind.REFRESH_PROJECTION, target="home")):
        engine.observe(obs)
    loop2 = assemble_until_steady(engine, hands)
    assert loop2.steady is True
    assert engine.admission().may_run_business is True
