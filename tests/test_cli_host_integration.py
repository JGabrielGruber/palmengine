"""CLI integration — ApplicationHost command and query paths."""

from __future__ import annotations

from bundles.standard.app.host.events import HostEventType
from bundles.standard.app.settings import PalmSettings
from palm.common.cqrs.query import ListInstancesQuery
from bundles.standard.runtimes.cli.shared.args import CliInvocation
from bundles.standard.runtimes.cli.shared.bootstrap import bootstrap_runtime, shutdown_context
from bundles.standard.runtimes.cli.tui import actions as tui_actions


def test_cli_submit_flow_uses_host_command_bus(fast_cli_settings: PalmSettings) -> None:
    dispatched: list[str] = []
    invocation = CliInvocation(command="flow", output_format="table")
    ctx = bootstrap_runtime(
        invocation=invocation,
        settings=fast_cli_settings,
        show_banner=False,
    )
    ctx.host.event.subscribe(
        HostEventType.COMMAND_DISPATCHED,
        lambda e: dispatched.append(str(e.payload.get("command"))),
    )
    try:
        from tests.helpers.flows import spine_wizard

        flow = spine_wizard("quick")
        ctx.app.runtime().repository.register_flow(flow)
        job = tui_actions.submit_flow(ctx, "quick")
        assert job.status.value == "WAITING_FOR_INPUT"
        ctx.host.provide_input(job.id, "ok")
        job = ctx.host.runtime().orchestration.get_job(job.id)
        assert job is not None
        assert job.status.value == "SUCCEEDED"
        assert "SubmitFlowCommand" in dispatched
    finally:
        shutdown_context(ctx)


def test_cli_context_requires_host(fast_cli_settings: PalmSettings) -> None:
    ctx = bootstrap_runtime(settings=fast_cli_settings, show_banner=False)
    try:
        assert ctx.host.is_started
        assert ctx.running_runtime_names() == ["main"]
        rows = ctx.host.ask(ListInstancesQuery(include_terminal=True))
        assert ctx.list_instance_summaries() == [] or len(rows) == len(
            ctx.list_instance_summaries()
        )
    finally:
        shutdown_context(ctx)


def test_cli_doctor_uses_projection_instance_list(fast_cli_settings: PalmSettings) -> None:
    from bundles.standard.runtimes.cli.commands.doctor import run_doctor

    ctx = bootstrap_runtime(settings=fast_cli_settings, show_banner=False)
    try:
        report = ctx.host.inspect.doctor(ctx.host.runtime())
        expected = 0 if report.get("status") == "ok" else 1
        assert run_doctor(ctx) == expected
        queried = ctx.host.ask(ListInstancesQuery(include_terminal=True))
        assert len(ctx.list_instance_summaries()) == len(queried)
    finally:
        shutdown_context(ctx)


def test_cli_runtime_binds_application_host(fast_cli_settings: PalmSettings) -> None:
    ctx = bootstrap_runtime(settings=fast_cli_settings, show_banner=False)
    try:
        runtime = ctx.host.runtime()
        assert runtime.application_host is ctx.host
        report = ctx.host.inspect.doctor(runtime)
        assert report["kind"] == "legacy_doctor"
        assert "start_plane_running" in report["control_plane"]
    finally:
        shutdown_context(ctx)


def test_cli_doctor_json_is_inspect_bag(fast_cli_settings: PalmSettings) -> None:
    from bundles.standard.runtimes.cli.commands.doctor import run_doctor

    ctx = bootstrap_runtime(
        settings=fast_cli_settings,
        show_banner=False,
        output_format="json",
    )
    try:
        report = ctx.host.inspect.doctor(ctx.host.runtime())
        expected = 0 if report.get("status") == "ok" else 1
        assert run_doctor(ctx) == expected
    finally:
        shutdown_context(ctx)
