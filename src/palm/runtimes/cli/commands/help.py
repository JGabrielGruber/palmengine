"""Help command — compact reference aligned with ApplicationHost command tiers."""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext


def cmd_help(ctx: CliContext, _args: list[str]) -> int:
    from rich.panel import Panel

    text = """
[bold cyan]Palm CLI[/] — ApplicationHost + CQRS

[bold]Host & diagnostics[/]
  status                    Live projection dashboard [green](default)[/]
  status --full             Detailed dashboard (active rows, traces)
  status -r [SEC]           Live refresh every SEC seconds (default 2)
  status --brief            Compact engine summary
  status <id>               Instance detail (job + wizard read models)
  doctor                    Full engine health report
  doctor --dashboard        Dashboard (supports --full / -r)

[bold]Flows[/] [dim](writes via host.submit_flow)[/]
  flow list                 All registered flows
  flow start <ref>          Start a flow [green](recommended)[/]
  start <ref>               Alias for flow start

[bold]Processes[/] [dim](multi-flow definitions)[/]
  process list              Catalog of process + flow definitions
  process submit <ref>        Start a process by name or id

[bold]Resources[/] [dim](declarative provider contracts — 0.12)[/]
  resource list             All registered resource definitions
  resource describe <ref>     Inspect provider, action, schemas, params

[bold]Instances[/] [dim](reads via host queries)[/]
  instance list [--all] [--status S] [--flow F] [--limit N] [--format json]
  instance resume <id>      Resume a persisted instance
  instance snapshots <id>   State snapshot history
  instance prune [--dry-run]  Remove terminal instances

[bold]Interactive[/] [dim](writes via host commands)[/]
  input [<id>] <value>      Provide wizard / branch input
  back [<id>] <step_slug>   Wizard backtrack

[bold]Deployment[/]
  host all-in-one           Collapsed master+worker (default profile)
  host master / worker / server

[bold]Legacy aliases[/] [dim](backward compatible)[/]
  definitions → process list · sessions → instance list
  instance status → status · process resume → instance resume
  wizard list/start/status/input → shortcuts (prefer flow/status/input)

[bold]System[/]
  version [--full]          Build info and registered plugins
  clear · help · exit
"""
    ctx.console.print(Panel(text.strip(), title="Help", border_style="cyan"))
    return 0