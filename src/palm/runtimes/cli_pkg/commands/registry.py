"""
Command registry — maps REPL/CLI phrases to handlers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from palm import __version__
from palm.runtimes.cli_pkg import actions
from palm.runtimes.cli_pkg.bootstrap import resolve_flow_ref, resolve_process_ref
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.cli_pkg.display import (
    render_definition_catalog,
    render_instance_table,
    render_job_status,
)

Handler = Callable[[CliContext, list[str]], int]


@dataclass
class CommandRegistry:
    """Ordered lookup: longest phrase match first."""

    handlers: dict[str, Handler] = field(default_factory=dict)

    def register(self, phrase: str, handler: Handler) -> None:
        self.handlers[phrase] = handler

    def dispatch(self, ctx: CliContext, line: str) -> int:
        import shlex

        parts = shlex.split(line.strip())
        if not parts:
            return 0

        for width in range(min(3, len(parts)), 0, -1):
            phrase = " ".join(parts[:width])
            handler = self.handlers.get(phrase)
            if handler is not None:
                return handler(ctx, parts[width:])

        ctx.console.print(
            f"[yellow]Unknown command:[/] {parts[0]}. Type [bold]help[/]."
        )
        return 1


def build_registry() -> CommandRegistry:
    reg = CommandRegistry()

    reg.register("help", _cmd_help)
    reg.register("status", _cmd_status)
    reg.register("version", _cmd_version)

    reg.register("process list", _cmd_process_list)
    reg.register("process submit", _cmd_process_submit)
    reg.register("process resume", _cmd_process_resume)

    reg.register("instance list", _cmd_instance_list)

    reg.register("wizard list", _cmd_wizard_list)
    reg.register("wizard start", _cmd_wizard_start)
    reg.register("wizard status", _cmd_wizard_status)
    reg.register("wizard input", _cmd_wizard_input)

    reg.register("input", _cmd_input)
    reg.register("back", _cmd_back)

    reg.register("sessions", _cmd_instance_list)
    reg.register("definitions", _cmd_process_list)
    reg.register("clear", _cmd_clear)
    reg.register("exit", _cmd_exit)
    reg.register("quit", _cmd_exit)

    return reg


def _cmd_help(ctx: CliContext, _args: list[str]) -> int:
    from rich.panel import Panel

    text = """
[bold cyan]Palm CLI[/] — EmbeddedRuntime commands

[bold]Definitions & processes[/]
  process list              List flow/process definitions (alias: definitions)
  process submit <ref>      Start a process by name or id
  process resume <id>       Resume a persisted instance

[bold]Instances[/]
  instance list             List process instances (alias: sessions)
  status [<instance_id>]    Job + wizard status (active instance if omitted)

[bold]Wizard[/]
  wizard list               Wizard-capable flows
  wizard start <flow>       Submit a wizard flow by name or id
  wizard status [<id>]      Same as status
  wizard input [<id>] <val> Same as input (backward compatible)

[bold]Interactive[/]
  input [<instance_id>] <value>
  back [<instance_id>] <step_slug>

[bold]System[/]
  clear                     Clear screen
  help                      This message
  exit / quit               Leave REPL
"""
    ctx.console.print(Panel(text.strip(), title="Help", border_style="cyan"))
    return 0


def _cmd_version(ctx: CliContext, _args: list[str]) -> int:
    ctx.console.print(f"Palm [bold]{__version__}[/]")
    return 0


def _cmd_status(ctx: CliContext, args: list[str]) -> int:
    try:
        iid = actions.resolve_instance_ref(ctx, args[0] if args else None)
    except (ValueError, Exception) as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    job = ctx.job_for_instance(iid)
    render_job_status(ctx.console, job, iid)
    return 0


def _cmd_process_list(ctx: CliContext, _args: list[str]) -> int:
    render_definition_catalog(ctx)
    return 0


def _cmd_instance_list(ctx: CliContext, _args: list[str]) -> int:
    instances = ctx.runtime.instances.list_instances()
    render_instance_table(ctx.console, instances)
    return 0


def _cmd_process_submit(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] process submit <process-name-or-id>")
        return 1
    try:
        resolve_process_ref(ctx.runtime, args[0])
        actions.submit_process(ctx, args[0])
        ctx.console.print("[dim]Process submitted.[/]")
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_process_resume(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] process resume <instance_id>")
        return 1
    try:
        actions.resume_instance(ctx, args[0])
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_wizard_list(ctx: CliContext, _args: list[str]) -> int:
    from rich.table import Table

    flows = [
        f
        for f in ctx.runtime.repository.list_flows()
        if f.pattern == "wizard"
    ]
    if not flows:
        ctx.console.print("[yellow]No wizard flows registered.[/]")
        return 0

    table = Table(title="Wizard Flows", show_lines=True)
    table.add_column("Name", style="green")
    table.add_column("ID", style="cyan")
    table.add_column("Pattern")
    for flow in flows:
        table.add_row(flow.name, flow.definition_id, flow.pattern)
    ctx.console.print(table)
    return 0


def _cmd_wizard_start(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] wizard start <flow_name_or_id>")
        return 1
    try:
        resolve_flow_ref(ctx.runtime, args[0])
        actions.submit_flow(ctx, args[0])
        ctx.console.print("[dim]Wizard started.[/]")
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_wizard_status(ctx: CliContext, args: list[str]) -> int:
    return _cmd_status(ctx, args)


def _cmd_wizard_input(ctx: CliContext, args: list[str]) -> int:
    return _cmd_input(ctx, args)


def _cmd_input(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] input [<instance_id>] <value>")
        return 1

    if len(args) == 1 and ctx.active_instance_id:
        iid = ctx.active_instance_id
        value = args[0]
    elif len(args) >= 2:
        try:
            iid = actions.resolve_instance_ref(ctx, args[0])
        except Exception as exc:
            ctx.console.print(f"[red]{exc}[/]")
            return 1
        value = " ".join(args[1:])
    else:
        ctx.console.print("[red]Usage:[/] input [<instance_id>] <value>")
        return 1

    try:
        actions.provide_input(ctx, iid, value)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_back(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] back [<instance_id>] <step_slug>")
        return 1

    if len(args) == 1 and ctx.active_instance_id:
        iid = ctx.active_instance_id
        target = args[0]
    elif len(args) >= 2:
        try:
            iid = actions.resolve_instance_ref(ctx, args[0])
        except Exception as exc:
            ctx.console.print(f"[red]{exc}[/]")
            return 1
        target = args[1]
    else:
        ctx.console.print("[red]Usage:[/] back [<instance_id>] <step_slug>")
        return 1

    try:
        actions.backtrack(ctx, iid, target)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_clear(ctx: CliContext, _args: list[str]) -> int:
    ctx.console.clear()
    return 0


def _cmd_exit(ctx: CliContext, _args: list[str]) -> int:
    raise EOFError()