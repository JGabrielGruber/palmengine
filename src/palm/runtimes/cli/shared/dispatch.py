"""
One-shot CLI dispatch — map parsed :class:`~palm.runtimes.cli.shared.args.CliInvocation`
to registry phrases.
"""

from __future__ import annotations

from palm.runtimes.cli.commands.registry import CommandRegistry
from palm.runtimes.cli.shared.args import CliInvocation
from palm.runtimes.cli.shared.context import CliContext


def dispatch_invocation(
    ctx: CliContext,
    registry: CommandRegistry,
    inv: CliInvocation,
) -> int:
    """Route a parsed one-shot invocation through the command registry."""
    if inv.command == "repl":
        raise ValueError("repl must be handled by run_repl()")

    line = _invocation_to_line(inv)
    if line is None:
        return 1
    return registry.dispatch(ctx, line)


def _invocation_to_line(inv: CliInvocation) -> str | None:
    if inv.command == "doctor":
        return "doctor --dashboard" if inv.dashboard else "doctor"

    if inv.command == "status":
        if inv.full:
            return "status --full"
        if inv.brief:
            return "status --brief"
        if inv.dashboard or not inv.instance_id:
            return "status --dashboard"
        return f"status {inv.instance_id}"

    if inv.command == "process":
        phrase = f"process {inv.process_cmd}"
        extra: list[str] = []
        if inv.process_cmd == "submit" and inv.ref:
            extra = [inv.ref]
        elif inv.process_cmd == "resume" and inv.instance_id:
            extra = [inv.instance_id]
        return " ".join([phrase, *extra]).strip()

    if inv.command == "instance":
        if inv.instance_cmd == "list":
            return " ".join(["instance list", *_instance_list_argv(inv)]).strip()
        if inv.instance_cmd == "status":
            ref = inv.instance_id or ""
            if ref:
                return f"status {ref}"
            return "status --dashboard"
        if inv.instance_cmd == "snapshots" and inv.instance_id:
            return f"instance snapshots {inv.instance_id}"
        if inv.instance_cmd == "resume" and inv.instance_id:
            return f"instance resume {inv.instance_id}"
        if inv.instance_cmd == "prune":
            extra = ["--dry-run"] if inv.prune_dry_run else []
            return " ".join(["instance prune", *extra]).strip()
        return None

    if inv.command == "flow":
        extra = [inv.flow] if inv.flow_cmd == "start" and inv.flow else []
        return " ".join([f"flow {inv.flow_cmd}", *extra]).strip()

    if inv.command == "start" and inv.flow:
        return f"start {inv.flow}"

    if inv.command == "wizard":
        extra = [inv.flow] if inv.wizard_cmd == "start" and inv.flow else []
        return " ".join([f"wizard {inv.wizard_cmd}", *extra]).strip()

    if inv.command == "input":
        return ("input " + " ".join(inv.input_args or [])).strip()

    if inv.command == "back":
        return ("back " + " ".join(inv.input_args or [])).strip()

    return None


def _instance_list_argv(inv: CliInvocation) -> list[str]:
    argv: list[str] = []
    if inv.instance_list_all:
        argv.append("--all")
    if inv.instance_status is not None:
        argv.extend(["--status", inv.instance_status])
    if inv.instance_flow is not None:
        argv.extend(["--flow", inv.instance_flow])
    if inv.instance_limit is not None:
        argv.extend(["--limit", str(inv.instance_limit)])
    if inv.output_format == "json":
        argv.extend(["--format", "json"])
    return argv