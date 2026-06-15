"""Help command — compact reference for command and REPL use."""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext


def cmd_help(ctx: CliContext, _args: list[str]) -> int:
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
