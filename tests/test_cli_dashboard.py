"""CLI status dashboard — projection-backed overview and host event recorder."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from palm.app import ApplicationHost, HostProfile, PalmSettings
from palm.app.host.event_recorder import HostEventRecorder
from palm.app.host.events import HostEventType
from palm.common.cqrs.query import ListWizardProgressQuery
from palm.runtimes.cli.cli import main
from palm.runtimes.cli.commands.dashboard import render_status_dashboard
from palm.runtimes.cli.commands.registry import build_registry
from palm.runtimes.cli.shared.bootstrap import bootstrap_runtime, shutdown_context


@pytest.fixture
def cli_ctx():
    ctx = bootstrap_runtime(show_banner=False)
    yield ctx
    shutdown_context(ctx)


def test_render_status_dashboard_smoke(cli_ctx) -> None:
    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    assert render_status_dashboard(cli_ctx) == 0
    output = buf.getvalue()
    assert "Status Dashboard" in output
    assert "Host" in output
    assert "Instances" in output
    assert "Active Wizards" in output
    assert "Recent Jobs" in output
    assert "Recent Host Events" in output


def test_status_dashboard_via_registry(cli_ctx) -> None:
    reg = build_registry()
    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    assert reg.dispatch(cli_ctx, "status --dashboard") == 0
    assert "Status Dashboard" in buf.getvalue()


def test_status_brief_via_registry(cli_ctx) -> None:
    reg = build_registry()
    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    assert reg.dispatch(cli_ctx, "status --brief") == 0
    output = buf.getvalue()
    assert "Palm Engine" in output
    assert "Status Dashboard" not in output


def test_main_status_default_is_dashboard(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["status"]) == 0
    output = capsys.readouterr().out
    assert "Status Dashboard" in output


def test_main_doctor_dashboard_flag(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["doctor", "--dashboard"]) == 0
    output = capsys.readouterr().out
    assert "Status Dashboard" in output


def test_host_event_recorder_ring_buffer() -> None:
    from palm.core.event import EventEngine

    engine = EventEngine()
    engine.initialize()
    recorder = HostEventRecorder(capacity=3)
    recorder.attach(engine)

    for index in range(5):
        engine.emit("test.event", count=index)

    recent = recorder.recent(limit=2)
    assert len(recent) == 2
    assert recent[0].type == "test.event"
    assert recent[0].payload["count"] == 3
    assert recent[1].payload["count"] == 4

    engine.emit("final", name="done")
    last = recorder.recent(limit=1)[-1]
    assert last.type == "final"
    assert last.payload["name"] == "done"

    recorder.shutdown()
    engine.shutdown()


def test_list_wizard_progress_query_active_only() -> None:
    settings = PalmSettings(load_example_definitions=True)
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    host.submit_flow("onboard")
    rows = host.list_wizard_progress_views(active_only=True)
    assert isinstance(rows, list)

    all_rows = host.ask(ListWizardProgressQuery(active_only=False))
    assert isinstance(all_rows, list)

    host.shutdown()


def test_last_recovery_populated_on_start() -> None:
    settings = PalmSettings(load_example_definitions=False)
    host = ApplicationHost(settings=settings, profile=HostProfile.all_in_one())
    host.start()

    recovery = host.last_recovery
    assert recovery is not None
    assert "workers" in recovery

    events = host.recent_host_events(limit=5)
    types = {event.type for event in events}
    assert HostEventType.RECOVERED in types or HostEventType.STARTED in types

    host.shutdown()