"""CLI command consolidation — diagnostics, aliases, and one-shot dispatch."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from palm.runtimes.cli.commands.registry import build_registry
from palm.runtimes.cli.shared.args import CliInvocation
from palm.runtimes.cli.shared.dispatch import dispatch_invocation


def test_status_default_is_dashboard(cli_ctx) -> None:
    reg = build_registry()
    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    assert reg.dispatch(cli_ctx, "status") == 0
    assert "Status Dashboard" in buf.getvalue()


def test_doctor_dashboard_flag_in_repl(cli_ctx) -> None:
    reg = build_registry()
    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    assert reg.dispatch(cli_ctx, "doctor --dashboard") == 0
    assert "Status Dashboard" in buf.getvalue()


def test_instance_status_without_id_routes_to_dashboard(cli_ctx) -> None:
    reg = build_registry()
    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    inv = CliInvocation(command="instance", instance_cmd="status")
    assert dispatch_invocation(cli_ctx, reg, inv) == 0
    assert "Status Dashboard" in buf.getvalue()


def test_process_resume_alias_uses_instance_resume() -> None:
    reg = build_registry()
    assert reg.handlers["process resume"] is reg.handlers["instance resume"]


def test_registry_aliases_match_catalog() -> None:
    from palm.runtimes.cli.commands.catalog import COMMAND_ALIASES

    reg = build_registry()
    for alias, canonical in COMMAND_ALIASES.items():
        assert alias in reg.handlers, alias
        assert canonical in reg.handlers, canonical
        assert reg.handlers[alias] is reg.handlers[canonical] or alias in {
            "start",
            "wizard list",
            "wizard start",
        }


@pytest.mark.parametrize(
    ("inv", "expected_prefix"),
    [
        (CliInvocation(command="status"), "status --dashboard"),
        (CliInvocation(command="status", brief=True), "status --brief"),
        (CliInvocation(command="status", full=True), "status --dashboard --full"),
        (CliInvocation(command="status", refresh_interval=2.0), "status --dashboard --refresh"),
        (CliInvocation(command="status", refresh_interval=5.0), "status --dashboard --refresh 5.0"),
        (CliInvocation(command="status", instance_id="abc"), "status abc"),
        (CliInvocation(command="doctor", dashboard=True), "doctor --dashboard"),
        (CliInvocation(command="instance", instance_cmd="status"), "status --dashboard"),
    ],
)
def test_invocation_dispatch_lines(inv: CliInvocation, expected_prefix: str) -> None:
    from palm.runtimes.cli.shared.dispatch import _invocation_to_line

    assert _invocation_to_line(inv) == expected_prefix
