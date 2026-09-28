"""0.61.1 — seat report protocol + dynamic walk + raw sampling."""

from __future__ import annotations

from typing import Any

from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime
from palm.system.subsystems.supervisor import CallableSystemService, SystemSupervisor
from palm.system.vitality import (
    KIND_OTHER,
    KIND_PLANE,
    LINEAGE_NATIVE,
    LINEAGE_SAMPLED,
    SEAT_BOOT_MEMBERSHIP,
    SEAT_EXECUTION,
    SEAT_REPORT_SCHEMA,
    SEAT_SESSION_PLANE,
    SEAT_SUPERVISOR,
    SEAT_SYSTEM_LOG,
    SEAT_WAIT_PLANE,
    SEAT_WORK_PLANE,
    STATE_ABSENT,
    STATE_OK,
    ProbeCatalog,
    SeatProbe,
    SeatReport,
    WalkOptions,
    coerce_report,
    default_probe_catalog,
    discover_seats,
    index_by_seat_id,
    seat_walk,
    supervisor_service_seat_id,
    walk_result,
)
from tests.helpers.bound import bound_for_runtime

# ── unit: SystemPlanes hub owns membership ───────────────────────────────────


def test_vitality_probes_planes_hub_not_private_plane_list() -> None:
    """Default catalog has the hub seat; members expand from the live hub."""
    from palm.system.vitality.schema import SEAT_PLANES
    from palm.system.vitality.seats import build_default_probes

    probes = build_default_probes()
    plane_kind = [p for p in probes if p.kind == KIND_PLANE]
    assert plane_kind == []  # no static wait/session/work probes
    assert any(p.seat_id == SEAT_PLANES for p in probes)


def test_started_runtime_planes_hub_consumes_members() -> None:
    rt = BaseRuntime()
    try:
        rt.start(drivers=bound_for_runtime(storage_backend="memory"))
        assert rt.planes is not None
        assert rt.planes.names() == ["wait", "session", "work"]
        assert rt.plane("wait") is rt.wait_plane
        assert rt.plane("wait_plane") is rt.wait_plane
        assert rt.plane("work") is rt.work_plane
        assert rt.session_plane is not None
    finally:
        rt.stop()


def test_system_planes_put_get_detach() -> None:
    from palm.system.subsystems.planes.hub import SystemPlanes

    hub = SystemPlanes()
    marker = object()
    hub.put("wait", marker, aliases=("wait_plane",))
    assert hub.get("wait") is marker
    assert hub.get("wait_plane") is marker
    assert hub.names() == ["wait"]
    assert hub.seat_id("wait") == "wait_plane"
    assert hub.detach() == ["wait"]
    assert hub.names() == []
    assert hub.get("wait") is None


def test_system_planes_install_owns_policy() -> None:
    """Planes subsystem install constructs + puts from runtime.install."""
    rt = BaseRuntime()
    try:
        rt.start(drivers=bound_for_runtime(storage_backend="memory"))
        hub = rt.planes
        assert hub is not None
        assert hub.names() == ["wait", "session", "work"]
        assert rt.install.orchestration is not None
        # Re-install from InstallInterface (not bag).
        names = hub.install(rt.install, {})
        assert names == ["wait", "session", "work"]
        assert rt.wait_plane is hub.get("wait")
        assert rt.session_plane is hub.get("session")
        assert rt.work_plane is hub.get("work")
    finally:
        rt.stop()


def test_system_planes_ensure_on_and_install_wait() -> None:
    from palm.system.interfaces.install import SystemInstall
    from palm.system.subsystems.planes.hub import SystemPlanes
    from palm.system.subsystems.planes.wait.plane import WaitPlaneService

    class _Orch:
        jobs: dict = {}

    class _Rt:
        def __init__(self) -> None:
            self.orchestration = _Orch()
            self.event = None
            self._planes = None
            self._install = SystemInstall()
            self._install.bind(
                orchestration=self.orchestration,
                event=None,
                submit=lambda *a, **k: None,
                able=lambda: False,
            )

        @property
        def install(self) -> SystemInstall:
            return self._install

    rt = _Rt()
    hub = SystemPlanes.ensure_on(rt)
    assert rt._planes is hub
    plane = hub.install_wait(rt.install)
    assert isinstance(plane, WaitPlaneService)
    assert hub.get("wait") is plane
    assert hub.get("wait_plane") is plane


def test_plane_definitions_at_edge_not_open_coded_on_hub() -> None:
    """SD-015: install law on definitions; hub walks catalog."""
    import inspect

    from palm.system.subsystems.planes.catalog import DEFAULT_PLANE_DEFINITIONS
    from palm.system.subsystems.planes.hub import SystemPlanes
    from palm.system.subsystems.planes.session.definition import SESSION_PLANE
    from palm.system.subsystems.planes.wait.definition import WAIT_PLANE
    from palm.system.subsystems.planes.work.definition import WORK_PLANE

    names = {d.name for d in DEFAULT_PLANE_DEFINITIONS}
    assert names == {"wait", "session", "work"}
    assert WAIT_PLANE.order < SESSION_PLANE.order < WORK_PLANE.order

    # Hub install body must not author wait/session/work attach prose.
    src = inspect.getsource(SystemPlanes.install)
    assert "WaitPlaneService" not in src
    assert "SessionPlaneService" not in src
    assert "WorkPlaneService" not in src
    assert "defn.install" in src or "definition" in src.lower()

    # Edge modules own the construct path.
    assert "WaitPlaneService" in inspect.getsource(WAIT_PLANE.install)
    assert "SessionPlaneService" in inspect.getsource(SESSION_PLANE.install)
    assert "WorkPlaneService" in inspect.getsource(WORK_PLANE.install)


def test_install_context_ports_not_runtime_bag_in_definitions() -> None:
    """CS-008: plane install signatures take InstallContext, not runtime."""
    import inspect

    from palm.system.subsystems.planes.session.definition import install_session_plane
    from palm.system.subsystems.planes.wait.definition import install_wait_plane
    from palm.system.subsystems.planes.work.definition import install_work_plane

    for fn in (install_wait_plane, install_session_plane, install_work_plane):
        sig = inspect.signature(fn)
        assert "ctx" in sig.parameters
        assert "runtime" not in sig.parameters


def test_supervisor_install_walks_definitions() -> None:
    """CS-006: schedule must not open-code continuous service construct."""
    import inspect

    from palm.system.boot.system_schedule import build_system_handlers
    from palm.system.subsystems.supervisor.definition import DEFAULT_CONTINUOUS_DEFINITIONS
    from palm.system.subsystems.supervisor.supervisor import SystemSupervisor

    names = {d.name for d in DEFAULT_CONTINUOUS_DEFINITIONS}
    # work_drain and outbox are DNA-listed organs. Hands register them. Wire must not freelance.
    assert "work_drain" not in names
    assert "outbox" not in names

    src = inspect.getsource(SystemSupervisor.install)
    assert "defn.register" in src

    # Schedule is catalog bind only (phase definitions own bodies)
    handlers_src = inspect.getsource(build_system_handlers)
    assert "CallableSystemService" not in handlers_src
    assert "OutboxLoopService" not in handlers_src
    assert "AuthMiddleware" not in handlers_src
    assert "bind_phase_handlers" in handlers_src
    assert "definitions_for_phases" in handlers_src

    from palm.system.boot.catalog import DEFAULT_SYSTEM_PHASE_DEFINITIONS
    from palm.system.boot.phases import system_phase_ids

    catalog_ids = {d.id for d in DEFAULT_SYSTEM_PHASE_DEFINITIONS}
    for pid in system_phase_ids():
        assert pid in catalog_ids, f"missing phase definition for {pid}"


def test_subsystem_protocol_and_package_layout() -> None:
    """SD-016: Subsystem protocol + interfaces/subsystems packages."""
    from palm.system.interfaces import InstallInterface, SystemInstall
    from palm.system.subsystems import Subsystem
    from palm.system.subsystems.planes.hub import SystemPlanes
    from palm.system.subsystems.supervisor import SystemSupervisor

    assert isinstance(SystemPlanes(), Subsystem)
    assert isinstance(SystemSupervisor(), Subsystem)
    assert issubclass(SystemInstall, object)
    assert isinstance(SystemInstall(), InstallInterface) or hasattr(
        SystemInstall(), "orchestration"
    )


def test_boot_context_publishes_seats() -> None:
    """BootContext gains install / planes / supervisor during system start."""
    from palm.system.boot.context import BootContext
    from palm.system.runtime.base import BaseRuntime

    rt = BaseRuntime()
    try:
        rt.start(drivers=bound_for_runtime(storage_backend="memory"))
        # Seats live on the shell after boot; BootContext is walk-local.
        assert rt.install is not None
        assert rt.planes is not None
        assert rt.supervisor is not None
        ctx = BootContext(
            schedule="system",
            shell=rt,
            install=rt.install,
            planes=rt.planes,
            supervisor=rt.supervisor,
        )
        assert ctx.shell is rt
        assert ctx.install is rt.install
        assert ctx.planes is rt.planes
        assert ctx.supervisor is rt.supervisor
    finally:
        rt.stop()


def test_boot_context_engine_seats_and_supervisor_ensure_on() -> None:
    """SD-016: boot publishes engine seats; supervisor seats like planes."""
    from palm.system.boot.context import BootContext
    from palm.system.boot.phases import SYSTEM_PHASES
    from palm.system.boot.system_schedule import build_system_handlers
    from palm.system.boot.walker import walk_schedule
    from palm.system.runtime.base import BaseRuntime
    from palm.system.subsystems.supervisor import SystemSupervisor

    rt = BaseRuntime()
    ctx = BootContext(schedule="system", shell=rt, runtime=str(rt.runtime_name))
    try:
        walk_schedule(
            SYSTEM_PHASES,
            build_system_handlers(
                options={
                    "drivers": bound_for_runtime(storage_backend="memory"),
                }
            ),
            ctx=ctx,
        )
        assert ctx.event is not None
        assert ctx.storage is not None
        assert ctx.orchestration is not None
        assert ctx.install is not None
        assert ctx.planes is not None
        assert ctx.supervisor is not None
        assert ctx.supervisor is rt.supervisor
        # ensure_on is idempotent seating
        again = SystemSupervisor.ensure_on(rt)
        assert again is rt.supervisor
    finally:
        rt.stop()


def test_runtime_install_is_first_class_interface() -> None:
    """SystemInstall peer of execution — bind explicit, snapshot via from_install."""
    from palm.system.interfaces.install import SystemInstall
    from palm.system.runtime.base import BaseRuntime
    from palm.system.subsystems.planes.install_context import InstallContext

    rt = BaseRuntime()
    assert isinstance(rt.install, SystemInstall)
    assert rt.install.orchestration is None
    rt.bind_system_install()
    assert rt.install.orchestration is rt.orchestration
    assert rt.install.submit is not None
    assert rt.install.able is not None
    # temporary alias
    assert rt.wire is rt.install

    ctx = InstallContext.from_install(
        rt.install,
        options={"work_plane_max_depth": 3},
        get_session_plane=lambda: None,
    )
    assert isinstance(ctx, InstallContext)
    assert ctx.options.get("work_plane_max_depth") == 3
    assert ctx.orchestration is rt.orchestration


# ── unit: SeatReport ─────────────────────────────────────────────────────────


def test_seat_report_roundtrip_and_schema() -> None:
    r = SeatReport.ok(
        "wait_plane",
        KIND_PLANE,
        load={},
        lineage=LINEAGE_SAMPLED,
        meta={"sample_source": "doctor_snapshot", "raw": {"open_wait_owners": 2}},
    )
    d = r.to_dict()
    assert d["schema"] == SEAT_REPORT_SCHEMA
    assert d["seat_id"] == "wait_plane"
    assert d["present"] is True
    assert d["state"] == STATE_OK
    assert d["lineage"] == LINEAGE_SAMPLED
    assert d["meta"]["raw"]["open_wait_owners"] == 2
    back = SeatReport.from_dict(d)
    assert back.seat_id == r.seat_id
    assert back.meta["raw"] == r.meta["raw"]


def test_seat_report_absent_never_present() -> None:
    r = SeatReport.absent("work_plane", KIND_PLANE, reason="not_attached")
    assert r.present is False
    assert r.state == STATE_ABSENT
    assert "not_attached" in r.notes


def test_seat_report_coerces_false_present_ok() -> None:
    r = SeatReport(
        seat_id="x",
        kind=KIND_OTHER,
        present=False,
        state=STATE_OK,
    )
    assert r.state == STATE_ABSENT


def test_coerce_report_fills_defaults() -> None:
    r = coerce_report({"state": "ok", "load": {"n": 1}}, default_seat_id="s1")
    assert r.seat_id == "s1"
    assert r.present is True
    assert r.load["n"] == 1


# ── unit: probe catalog ──────────────────────────────────────────────────────


def test_probe_catalog_register_clone_extend() -> None:
    cat = ProbeCatalog()
    cat.register(
        SeatProbe(
            seat_id="alpha",
            kind=KIND_OTHER,
            resolve=lambda inst: getattr(inst, "alpha", None),
            order=1,
        )
    )
    clone = cat.clone()
    clone.register(
        SeatProbe(
            seat_id="beta",
            kind=KIND_OTHER,
            resolve=lambda inst: None,
            order=2,
        )
    )
    assert "alpha" in cat
    assert "beta" not in cat
    assert clone.seat_ids() == ["alpha", "beta"]


def test_default_probe_catalog_has_core_seeds() -> None:
    from palm.system.vitality.schema import SEAT_PLANES

    ids = set(default_probe_catalog().seat_ids())
    for sid in (
        SEAT_PLANES,
        SEAT_SUPERVISOR,
        SEAT_EXECUTION,
        SEAT_SYSTEM_LOG,
        SEAT_BOOT_MEMBERSHIP,
    ):
        assert sid in ids
    # Plane members are expanded from the hub — not static probes.
    assert SEAT_WAIT_PLANE not in ids
    assert SEAT_SESSION_PLANE not in ids
    assert SEAT_WORK_PLANE not in ids


def test_first_resolver_picks_first_non_none() -> None:
    from palm.system.vitality.probe import attr_resolver, first_resolver

    class _Shell:
        named = None
        other = "kept"

    resolve = first_resolver(attr_resolver("named"), attr_resolver("other"))
    assert resolve(_Shell()) == "kept"


def test_default_probes_use_shared_resolvers() -> None:
    """Seat table uses attr_resolver / hub / first_resolver — no getattr wrappers."""
    import palm.system.vitality.seats as seats
    from palm.system.subsystems.planes.hub import get_system_planes
    from palm.system.vitality.schema import SEAT_INSTALL, SEAT_PLANES, SEAT_STRUCTURE
    from palm.system.vitality.seats import build_default_probes

    for name in (
        "_resolve_execution",
        "_resolve_install",
        "_resolve_system_log",
        "_resolve_planes",
        "_resolve_structure",
    ):
        assert not hasattr(seats, name), name

    probes = {p.seat_id: p for p in build_default_probes()}

    def attr_names(resolve: object) -> tuple[str, ...]:
        assert getattr(resolve, "__qualname__", "") == "attr_resolver.<locals>._resolve"
        closure = getattr(resolve, "__closure__", None)
        assert closure is not None
        return closure[0].cell_contents

    assert attr_names(probes[SEAT_SUPERVISOR].resolve) == ("supervisor",)
    assert attr_names(probes[SEAT_EXECUTION].resolve) == ("execution",)
    assert attr_names(probes[SEAT_INSTALL].resolve) == ("install",)
    assert attr_names(probes[SEAT_STRUCTURE].resolve) == ("structure",)
    assert probes[SEAT_PLANES].resolve is get_system_planes
    boot = probes[SEAT_BOOT_MEMBERSHIP].resolve
    assert getattr(boot, "__qualname__", "") == "private_attr_resolver.<locals>._resolve"
    slog = probes[SEAT_SYSTEM_LOG].resolve
    assert getattr(slog, "__qualname__", "") == "first_resolver.<locals>._resolve"
    assert probes[SEAT_SYSTEM_LOG].report_instance is None


# ── lean shell: honest absent ────────────────────────────────────────────────


class _LeanShell:
    """Minimal duck-typed instance with no planes attached."""

    is_started = False


def test_walk_lean_shell_honest_absent() -> None:
    from palm.system.vitality.schema import SEAT_PLANES

    reset_system_log_for_tests()
    reports = discover_seats(
        _LeanShell(),
        expand_supervisor_services="never",
        expand_planes="never",
    )
    by_id = index_by_seat_id(reports)

    assert by_id[SEAT_PLANES].state == STATE_ABSENT
    assert by_id[SEAT_PLANES].present is False
    # Members not expanded when hub is absent.
    assert SEAT_WAIT_PLANE not in by_id
    assert SEAT_SESSION_PLANE not in by_id
    assert SEAT_WORK_PLANE not in by_id
    assert by_id[SEAT_SUPERVISOR].state == STATE_ABSENT
    assert by_id[SEAT_BOOT_MEMBERSHIP].state == STATE_ABSENT

    # Process log still present (process-wide seat); raw-sampled public API.
    assert by_id[SEAT_SYSTEM_LOG].present is True
    assert by_id[SEAT_SYSTEM_LOG].lineage == LINEAGE_SAMPLED
    assert "raw" in by_id[SEAT_SYSTEM_LOG].meta

    # Execution absent: lean shell has no port methods.
    assert by_id[SEAT_EXECUTION].state == STATE_ABSENT


def test_walk_no_fake_green_for_missing_planes() -> None:
    from palm.system.vitality.schema import SEAT_PLANES

    reports = discover_seats(_LeanShell())
    by_id = index_by_seat_id(reports)
    assert by_id[SEAT_PLANES].present is False
    assert by_id[SEAT_PLANES].state == STATE_ABSENT
    for sid in (SEAT_WAIT_PLANE, SEAT_SESSION_PLANE, SEAT_WORK_PLANE):
        assert sid not in by_id


# ── full BaseRuntime attach ──────────────────────────────────────────────────


def test_walk_started_base_runtime_seats_present() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(
        drivers=bound_for_runtime(storage_backend="memory"), structure_definition_id="local.cli"
    )
    try:
        result = walk_result(rt)
        by_id = result.by_id()

        from palm.system.vitality.schema import SEAT_PLANES

        for sid in (
            SEAT_PLANES,
            SEAT_WAIT_PLANE,
            SEAT_SESSION_PLANE,
            SEAT_WORK_PLANE,
            SEAT_SUPERVISOR,
            SEAT_EXECUTION,
            SEAT_SYSTEM_LOG,
            SEAT_BOOT_MEMBERSHIP,
        ):
            assert sid in by_id, f"missing seat {sid}"
            assert by_id[sid].present is True, f"{sid} should be present"
            assert by_id[sid].state == STATE_OK, f"{sid} state={by_id[sid].state}"

        # Boot membership saw phases (raw under meta).
        boot = by_id[SEAT_BOOT_MEMBERSHIP]
        assert boot.lineage == LINEAGE_SAMPLED
        assert boot.meta.get("raw", {}).get("count", 0) > 0

        # Planes / supervisor / log: raw public APIs — product presents.
        assert by_id[SEAT_WAIT_PLANE].lineage == LINEAGE_SAMPLED
        assert by_id[SEAT_WAIT_PLANE].meta.get("sample_source") == "doctor_snapshot"
        assert "raw" in by_id[SEAT_WAIT_PLANE].meta
        assert by_id[SEAT_SESSION_PLANE].lineage == LINEAGE_SAMPLED
        assert by_id[SEAT_WORK_PLANE].lineage == LINEAGE_SAMPLED
        assert by_id[SEAT_WORK_PLANE].meta.get("sample_source") == "status"
        assert by_id[SEAT_SUPERVISOR].lineage == LINEAGE_SAMPLED
        assert by_id[SEAT_SYSTEM_LOG].lineage == LINEAGE_SAMPLED
        assert "capacity" in (by_id[SEAT_SYSTEM_LOG].meta.get("raw") or {})

        # Dynamic supervisor services (work_drain, outbox when DNA lists them).
        service_ids = [r.seat_id for r in result.reports if r.seat_id.startswith("supervisor.")]
        assert supervisor_service_seat_id("work_drain") in service_ids
        assert supervisor_service_seat_id("outbox") in service_ids
        for sid in service_ids:
            assert by_id[sid].present is True
            assert by_id[sid].lineage == LINEAGE_SAMPLED
            assert "raw" in by_id[sid].meta

        assert result.present_count >= 7
        assert result.error_count == 0
    finally:
        rt.stop()


def test_seat_walk_dicts_schema() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        rows = seat_walk(rt)
        assert all(row["schema"] == SEAT_REPORT_SCHEMA for row in rows)
        assert any(row["seat_id"] == SEAT_WAIT_PLANE for row in rows)
    finally:
        rt.stop()


def test_public_last_boot_walk_property() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    assert rt.last_boot_walk is None
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.last_boot_walk is not None
        assert len(rt.last_boot_walk) > 0
    finally:
        rt.stop()


# ── detach / dynamics ────────────────────────────────────────────────────────


def test_detach_wait_plane_becomes_absent() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        before = index_by_seat_id(discover_seats(rt))
        assert before[SEAT_WAIT_PLANE].present is True

        hub = rt.planes
        assert hub is not None
        hub.remove("wait")

        after = index_by_seat_id(discover_seats(rt))
        # Removed from hub → no longer expanded as a member seat.
        assert SEAT_WAIT_PLANE not in after or after[SEAT_WAIT_PLANE].present is False
        assert after[SEAT_SESSION_PLANE].present is True
        assert rt.wait_plane is None
    finally:
        rt.stop()


def test_supervisor_service_discovered_dynamically() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.supervisor is not None
        custom = CallableSystemService("custom_loop", status=lambda: {"ticks": 3})
        rt.supervisor.register(custom)

        by_id = index_by_seat_id(discover_seats(rt))
        sid = supervisor_service_seat_id("custom_loop")
        assert sid in by_id
        assert by_id[sid].present is True
        assert by_id[sid].meta.get("raw", {}).get("ticks") == 3
    finally:
        rt.stop()


def test_expand_supervisor_services_never() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        reports = discover_seats(rt, WalkOptions(expand_supervisor_services="never"))
        assert all(not r.seat_id.startswith("supervisor.") for r in reports)
        assert any(r.seat_id == SEAT_SUPERVISOR for r in reports)
    finally:
        rt.stop()


# ── native vs raw lineage ────────────────────────────────────────────────────


def test_native_seat_report_preferred_over_raw() -> None:
    from palm.system.subsystems.planes.hub import SystemPlanes

    class _NativePlane:
        def doctor_snapshot(self) -> dict[str, Any]:
            return {"wait_plane_attached": True, "open_wait_owners": 99}

        def seat_report(self) -> dict[str, Any]:
            return {
                "schema": SEAT_REPORT_SCHEMA,
                "seat_id": SEAT_WAIT_PLANE,
                "kind": KIND_PLANE,
                "present": True,
                "state": STATE_OK,
                "load": {"open_wait_owners": 1, "native": True},
                "notes": ["from_native"],
                "lineage": LINEAGE_NATIVE,
            }

    hub = SystemPlanes()
    hub.put("wait", _NativePlane(), aliases=("wait_plane",))

    class _Shell:
        is_started = True
        _planes = hub
        supervisor = None
        execution = None
        last_boot_walk = None

    cat = default_probe_catalog()
    reports = discover_seats(
        _Shell(),
        WalkOptions(
            catalog=cat,
            expand_supervisor_services="never",
            expand_planes="when_present",
            skip_seat_ids=frozenset(
                {
                    SEAT_SUPERVISOR,
                    SEAT_EXECUTION,
                    SEAT_BOOT_MEMBERSHIP,
                    SEAT_SYSTEM_LOG,
                }
            ),
        ),
    )
    by_id = index_by_seat_id(reports)
    wait = by_id[SEAT_WAIT_PLANE]
    assert wait.lineage == LINEAGE_NATIVE
    assert wait.load.get("native") is True
    assert wait.load.get("open_wait_owners") == 1
    assert "from_native" in wait.notes


def test_system_log_and_supervisor_have_no_seat_report() -> None:
    """Seats expose public API; vitality samples raw — product presents."""
    reset_system_log_for_tests()
    from palm.system.log import get_system_log

    log = get_system_log()
    assert not hasattr(log, "seat_report") or not callable(getattr(type(log), "seat_report", None))
    assert log.capacity >= 10
    assert isinstance(log.record_count, int)

    sup = SystemSupervisor()
    sup.register(CallableSystemService("x"))
    assert not hasattr(SystemSupervisor, "seat_report")
    assert "x" in sup.status()["registered"]


# ── custom probe extension ───────────────────────────────────────────────────


def test_custom_probe_extends_discovery() -> None:
    class _Shell:
        is_started = True
        custom_seat = object()

    cat = ProbeCatalog()
    cat.register(
        SeatProbe(
            seat_id="custom_seat",
            kind=KIND_OTHER,
            resolve=lambda inst: getattr(inst, "custom_seat", None),
            report=lambda inst, seat: SeatReport.ok(
                "custom_seat",
                KIND_OTHER,
                load={"found": True},
                lineage=LINEAGE_NATIVE,
            ),
            order=1,
        )
    )
    reports = discover_seats(
        _Shell(),
        WalkOptions(catalog=cat, expand_supervisor_services="never"),
    )
    assert len(reports) == 1
    assert reports[0].seat_id == "custom_seat"
    assert reports[0].load["found"] is True


def test_probe_error_becomes_error_report() -> None:
    def _bad_resolve(inst: Any) -> Any:
        raise RuntimeError("boom")

    cat = ProbeCatalog()
    cat.register(
        SeatProbe(
            seat_id="bad",
            kind=KIND_OTHER,
            resolve=_bad_resolve,
            order=1,
        )
    )
    reports = discover_seats(
        object(),
        WalkOptions(catalog=cat, expand_supervisor_services="never"),
    )
    assert len(reports) == 1
    assert reports[0].state == "error"
    assert "boom" in reports[0].notes[0]


# ── observation purity ───────────────────────────────────────────────────────


def test_walk_does_not_start_supervisor_services() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(drivers=bound_for_runtime(storage_backend="memory"))
    try:
        assert rt.supervisor is not None
        assert rt.supervisor.status()["running_count"] == 0
        discover_seats(rt)
        assert rt.supervisor.status()["running_count"] == 0
    finally:
        rt.stop()


def test_system_package_exports_vitality_importable() -> None:
    import palm.system.vitality as vit

    assert vit.SEAT_REPORT_SCHEMA == "palm.seat_report/1"
    assert callable(vit.discover_seats)
