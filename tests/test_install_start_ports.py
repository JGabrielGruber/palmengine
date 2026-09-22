"""Install board is the only writer of work_drain start ports."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.boot.modes import BootMode
from bundles.standard.app.settings import PalmSettings
from palm.core.structure import LOCAL_CLI_ID
from palm.system.interfaces.install import SystemInstall
from palm.system.log import reset_system_log_for_tests
from palm.system.runtime.base import BaseRuntime


class _FakePlane:
    def __init__(self) -> None:
        self._submit_flow = None
        self._able = None
        self.is_attached = True

    def set_submit_flow(self, submit) -> None:
        self._submit_flow = submit

    def set_able(self, able) -> None:
        self._able = able


def test_bind_pushes_submit_and_able_onto_plane() -> None:
    board = SystemInstall()
    plane = _FakePlane()

    def submit(flow_id: str, payload: dict) -> str:
        return flow_id

    def able() -> bool:
        return True

    board.bind(work_plane=plane, submit=submit, able=able)
    assert board.start_ports_bound() is True
    assert plane._submit_flow is submit
    assert plane._able is able


def test_rebind_replaces_plane_ports() -> None:
    board = SystemInstall()
    plane = _FakePlane()
    board.bind(work_plane=plane, submit=lambda *_a: "old", able=lambda: False)

    def new_submit(*_a):
        return "new"

    board.bind(submit=new_submit, able=lambda: True)
    assert plane._submit_flow is new_submit
    assert plane._able() is True


def test_host_cli_binds_start_ports_on_install_not_defer() -> None:
    reset_system_log_for_tests()
    host = ApplicationHost.for_mode(
        BootMode.cli(),
        settings=PalmSettings.for_tests(load_examples=False),
    )
    host.start()
    try:
        rt = host.runtime()
        assert rt.install.start_ports_bound() is True
        assert host.admission.definition_id == LOCAL_CLI_ID
        assert rt.work_plane is not None
        assert rt.work_plane.is_running is True
        assert rt.install.submit is rt.work_plane._submit_flow
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.background.start"].outcome == "ok"
        assert "defer_work_drain_start" not in (rt._start_options or {})
    finally:
        host.shutdown()


def test_bare_runtime_cli_starts_drain_when_ports_bound() -> None:
    reset_system_log_for_tests()
    rt = BaseRuntime()
    rt.start(storage_backend="memory", structure_definition_id=LOCAL_CLI_ID)
    try:
        assert rt.install.start_ports_bound() is True
        assert "work_drain" in rt.supervisor.names()
        by_id = {w.phase: w for w in (rt._last_boot_walk or [])}
        assert by_id["system.background.start"].outcome == "ok"
        assert rt.supervisor.get("work_drain").is_running is True
    finally:
        rt.stop()
