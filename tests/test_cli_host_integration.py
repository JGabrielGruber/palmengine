"""CLI integration — ApplicationHost command and query paths."""

from __future__ import annotations

from palm.app.host.events import HostEventType
from palm.app.settings import PalmSettings
from palm.common.cqrs.query import ListInstancesQuery
from palm.definitions.flow import FlowDefinition
from palm.runtimes.cli.shared.args import CliInvocation
from palm.runtimes.cli.shared.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli.tui import actions as tui_actions


def test_cli_submit_flow_uses_host_command_bus() -> None:
    dispatched: list[str] = []
    invocation = CliInvocation(command="flow", output_format="table")
    ctx = bootstrap_runtime(invocation=invocation, show_banner=False)
    ctx.host.event.subscribe(
        HostEventType.COMMAND_DISPATCHED,
        lambda e: dispatched.append(str(e.payload.get("command"))),
    )
    try:
        flow = FlowDefinition(name="quick", pattern="dag", options={"name": "quick"})
        ctx.app.runtime().repository.register_flow(flow)
        job = tui_actions.submit_flow(ctx, "quick")
        assert job.status.value == "SUCCEEDED"
        assert "SubmitFlowCommand" in dispatched
    finally:
        shutdown_context(ctx)


def test_cli_context_requires_host() -> None:
    ctx = bootstrap_runtime(show_banner=False)
    try:
        assert ctx.host.is_started
        assert ctx.running_runtime_names() == ["main"]
        rows = ctx.host.ask(ListInstancesQuery(include_terminal=True))
        assert ctx.list_instance_summaries() == [] or len(rows) == len(ctx.list_instance_summaries())
    finally:
        shutdown_context(ctx)


def test_cli_doctor_uses_projection_instance_list() -> None:
    from palm.runtimes.cli.commands.doctor import run_doctor

    ctx = bootstrap_runtime(show_banner=False)
    try:
        assert run_doctor(ctx) == 0
        queried = ctx.host.ask(ListInstancesQuery(include_terminal=True))
        assert len(ctx.list_instance_summaries()) == len(queried)
    finally:
        shutdown_context(ctx)