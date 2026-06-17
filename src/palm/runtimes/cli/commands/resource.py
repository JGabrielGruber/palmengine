"""Resource commands — list and describe declarative resource definitions."""

from __future__ import annotations

import json

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.resource_labels import resource_detail_label


def cmd_resource_list(ctx: CliContext, _args: list[str]) -> int:
    from rich.table import Table

    resources = ctx.app.list_resources()
    if not resources:
        ctx.console.print("[yellow]No resources registered.[/]")
        return 0

    table = Table(title="Registered Resources", show_lines=True)
    table.add_column("Name", style="green")
    table.add_column("ID", style="cyan")
    table.add_column("Provider")
    table.add_column("Action", style="dim")
    table.add_column("Detail", style="dim")
    for resource in resources:
        table.add_row(
            resource.name,
            resource.definition_id,
            resource.provider,
            resource.action,
            resource_detail_label(resource),
        )
    ctx.console.print(table)
    ctx.console.print(
        "[dim]Inspect a resource:[/] [cyan]resource describe <name-or-id>[/]"
    )
    return 0


def cmd_resource_describe(ctx: CliContext, args: list[str]) -> int:
    from rich.panel import Panel
    from rich.table import Table

    if not args:
        ctx.console.print("[red]Usage:[/] resource describe <resource_name_or_id>")
        return 1

    try:
        resource = ctx.resolve_resource(args[0])
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1

    description = ""
    if isinstance(resource.metadata, dict):
        description = str(resource.metadata.get("description") or "")

    header = (
        f"[bold]{resource.name}[/] [dim]({resource.definition_id})[/]\n"
        f"Provider: [cyan]{resource.provider}[/] · Action: [cyan]{resource.action}[/]"
    )
    if description:
        header = f"{header}\n{description}"
    ctx.console.print(Panel(header.strip(), title="Resource", border_style="green"))

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="dim")
    table.add_column("Value")
    if resource.resource_id:
        table.add_row("resource_id", resource.resource_id)
    if resource.output_key:
        table.add_row("output_key", resource.output_key)
    if resource.params:
        table.add_row("params", json.dumps(resource.params, indent=2))
    if resource.metadata:
        table.add_row("metadata", json.dumps(resource.metadata, indent=2))
    ctx.console.print(table)

    if resource.input_schema:
        ctx.console.print(
            Panel(
                json.dumps(resource.input_schema, indent=2),
                title="Input schema",
                border_style="blue",
            )
        )
    if resource.output_schema:
        ctx.console.print(
            Panel(
                json.dumps(resource.output_schema, indent=2),
                title="Output schema",
                border_style="blue",
            )
        )
    return 0