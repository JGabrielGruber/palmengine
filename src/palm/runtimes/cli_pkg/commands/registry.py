"""
Command registry — maps REPL/CLI phrases to handlers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from palm import __version__
from palm.core.registry import pattern_registry, storage_registry
from palm.runtimes.cli_pkg import actions
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.cli_pkg.display import (
    render_definition_catalog,
    render_instance_table,
    render_job_status,
)
from palm.runtimes.cli_pkg.doctor import run_doctor
from palm.runtimes.cli_pkg.instance_ops import (
    filter_summaries,
    parse_instance_list_flags,
    prune_terminal_instances,
)
from palm.runtimes.cli_pkg.output import emit_json, snapshots_to_json, summaries_payload

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

        ctx.console.print(f"[yellow]Unknown command:[/] {parts[0]}. Type [bold]help[/].")
        return 1


def build_registry() -> CommandRegistry:
    reg = CommandRegistry()

    reg.register("help", _cmd_help)
    reg.register("doctor", _cmd_doctor)
    reg.register("status", _cmd_status)
    reg.register("version", _cmd_version)

    reg.register("process list", _cmd_process_list)
    reg.register("process submit", _cmd_process_submit)
    reg.register("process resume", _cmd_process_resume)

    reg.register("flow list", _cmd_flow_list)
    reg.register("flow start", _cmd_flow_start)
    reg.register("start", _cmd_start)

    reg.register("instance list", _cmd_instance_list)
    reg.register("instance snapshots", _cmd_instance_snapshots)
    reg.register("instance status", _cmd_status)
    reg.register("instance resume", _cmd_process_resume)
    reg.register("instance prune", _cmd_instance_prune)

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

[bold]Flows[/]
  flow list                 All registered flows (any pattern)
  flow start <ref>          Start a flow by name or id [green](recommended)[/]
  start <ref>               Shortcut for flow start

[bold]Definitions & processes[/]
  process list              List flow/process definitions (alias: definitions)
  process submit <ref>      Start a process by name or id
  process resume <id>       Resume a persisted instance

[bold]Instances[/]
  instance list [--all] [--status S] [--flow F] [--limit N] [--format json]
  instance status [<id>]    Job + wizard status (alias: status)
  instance snapshots <id>   State snapshot history for an instance
  instance resume <id>        Resume a persisted instance
  instance prune [--dry-run]  Remove terminal instances from storage
  status [<instance_id>]      Same as instance status

[bold]Wizard[/] [dim](shortcut — prefer flow start)[/]
  wizard list               Wizard-capable flows
  wizard start <flow>       Start a flow (alias; use flow start for parallel/dag/etl)
  wizard status [<id>]      Same as status
  wizard input [<id>] <val> Same as input (backward compatible)

[bold]Interactive[/]
  input [<instance_id>] <value>
  back [<instance_id>] <step_slug>

[bold]Diagnostics[/]
  doctor                    Full engine health report
  version --full            Build info and registered plugins
  status --full             Same as doctor (one-shot: palm status --full)

[bold]System[/]
  clear                     Clear screen
  help                      This message
  exit / quit               Leave REPL
"""
    ctx.console.print(Panel(text.strip(), title="Help", border_style="cyan"))
    return 0


def _cmd_version(ctx: CliContext, args: list[str]) -> int:
    from palm.runtimes.cli_pkg.version_info import print_version_brief, print_version_full

    if args and args[0] == "--full":
        return print_version_full(ctx.console)
    print_version_brief()
    return 0


def _cmd_doctor(ctx: CliContext, _args: list[str]) -> int:
    return run_doctor(ctx)


def _cmd_status(ctx: CliContext, args: list[str]) -> int:
    if args and args[0] == "--full":
        return run_doctor(ctx)
    if not args and not ctx.active_instance_id:
        return _cmd_engine_status(ctx)
    try:
        ref = args[0] if args else None
        iid = actions.resolve_instance_ref(ctx, ref)
    except (ValueError, Exception) as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    job = ctx.job_for_instance(iid)
    if ctx.output_format == "json":
        from palm.runtimes.cli_pkg.job_context import inspect_job_json

        payload: dict[str, object] = {
            "instance_id": iid,
            "job_id": job.id,
            "status": job.status.value,
            **inspect_job_json(job),
        }
        emit_json(ctx.console, payload)
        return 0
    render_job_status(ctx.console, job, iid)
    return 0


def _cmd_engine_status(ctx: CliContext) -> int:
    from rich.panel import Panel

    ctx.console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            f"Runtime: embedded — "
            f"{'[green]started[/]' if ctx.app.is_runtime_started() else '[red]stopped[/]'}\n"
            f"Patterns: {', '.join(pattern_registry.names())}\n"
            f"Storage:  {', '.join(storage_registry.names())}\n\n"
            f"[dim]Tip:[/] [cyan]flow start <name>[/] to run a flow, "
            f"[cyan]doctor[/] for health, [cyan]status <id>[/] for detail",
            title="Status",
            border_style="green",
        )
    )
    return 0


def _cmd_process_list(ctx: CliContext, _args: list[str]) -> int:
    render_definition_catalog(ctx)
    return 0


def _cmd_instance_list(ctx: CliContext, args: list[str]) -> int:
    options, _remaining = parse_instance_list_flags(args)
    if "--format" in args:
        index = args.index("--format")
        if index + 1 < len(args) and args[index + 1] == "json":
            ctx.output_format = "json"

    summaries = filter_summaries(
        ctx.list_instance_summaries(),
        options=options,
    )
    if ctx.output_format == "json":
        emit_json(ctx.console, summaries_payload(summaries))
        return 0

    hint = None
    if not options.include_all:
        hint = (
            "Showing active (non-terminal) instances — append [cyan]--all[/] to include completed."
        )
    render_instance_table(ctx.console, summaries, hint=hint)
    return 0


def _cmd_instance_snapshots(ctx: CliContext, args: list[str]) -> int:
    from rich.table import Table

    if not args:
        ctx.console.print("[red]Usage:[/] instance snapshots <instance_id>")
        return 1
    try:
        instance_id = ctx.resolve_instance_id(args[0])
        snapshots = ctx.list_instance_snapshots(instance_id)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    if ctx.output_format == "json":
        emit_json(
            ctx.console,
            {"instance_id": instance_id, "snapshots": snapshots_to_json(snapshots)},
        )
        return 0

    if not snapshots:
        ctx.console.print("[yellow]No state snapshots recorded for this instance.[/]")
        ctx.console.print(
            "[dim]Enable with[/] [cyan]PALM_ENABLE_STATE_SNAPSHOT=true[/] "
            "[dim]or[/] [cyan]--enable-state-snapshot[/]"
        )
        return 0

    table = Table(title=f"State Snapshots — {instance_id[:20]}", show_lines=True)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Status", style="yellow")
    table.add_column("Recorded At", style="cyan")
    table.add_column("Step")
    table.add_column("Job", style="dim")
    for index, snapshot in enumerate(snapshots, start=1):
        table.add_row(
            str(index),
            snapshot.status,
            snapshot.recorded_at,
            snapshot.wizard_step_slug or "—",
            snapshot.job_id[:14],
        )
    ctx.console.print(table)
    return 0


def _cmd_process_submit(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] process submit <process-name-or-id>")
        return 1
    try:
        ctx.app.resolve_process(args[0])
        actions.submit_process(ctx, args[0])
        ctx.console.print("[dim]Process submitted.[/]")
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_instance_prune(ctx: CliContext, args: list[str]) -> int:
    dry_run = "--dry-run" in args
    removed = prune_terminal_instances(ctx, dry_run=dry_run)
    if ctx.output_format == "json":
        emit_json(ctx.console, {"dry_run": dry_run, "removed": removed})
        return 0
    label = "Would remove" if dry_run else "Removed"
    if not removed:
        ctx.console.print("[dim]No terminal instances to prune.[/]")
        return 0
    ctx.console.print(f"[green]{label}[/] {len(removed)} instance(s):")
    for instance_id in removed:
        ctx.console.print(f"  • {instance_id}")
    return 0


def _cmd_process_resume(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] process resume <instance_id>")
        return 1
    try:
        instance_id = ctx.resolve_instance_id(args[0])
        actions.resume_instance(ctx, instance_id)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_flow_list(ctx: CliContext, _args: list[str]) -> int:
    from rich.table import Table

    flows = ctx.app.list_flows()
    if not flows:
        ctx.console.print("[yellow]No flows registered.[/]")
        return 0

    table = Table(title="Registered Flows", show_lines=True)
    table.add_column("Name", style="green")
    table.add_column("ID", style="cyan")
    table.add_column("Pattern")
    table.add_column("Schema", style="dim")
    table.add_column("Detail", style="dim")
    for flow in flows:
        schema = "flow" if flow.has_state_schema else "—"
        from palm.runtimes.cli_pkg.display import flow_detail_label

        table.add_row(flow.name, flow.definition_id, flow.pattern, schema, flow_detail_label(flow))
    ctx.console.print(table)
    ctx.console.print(
        "[dim]Start any flow:[/] [cyan]flow start <name>[/] or [cyan]start <name>[/]"
    )
    return 0


def _cmd_flow_start(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] flow start <flow_name_or_id>")
        return 1
    try:
        actions.start_flow(ctx, args[0])
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def _cmd_start(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] start <flow_name_or_id>  [dim](alias: flow start)[/]")
        return 1
    return _cmd_flow_start(ctx, args)


def _cmd_wizard_list(ctx: CliContext, _args: list[str]) -> int:
    from rich.table import Table

    flows = [f for f in ctx.app.list_flows() if f.pattern == "wizard"]
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
        actions.start_flow(ctx, args[0], via_shortcut="wizard")
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
