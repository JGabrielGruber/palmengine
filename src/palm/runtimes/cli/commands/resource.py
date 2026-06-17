"""Resource commands — list, describe, and invoke resource definitions."""

from __future__ import annotations

import json

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.resource_labels import resource_detail_label


def _parse_key_values(tokens: list[str]) -> dict[str, str]:
    """Parse ``key=value`` tokens for state binding and param overrides."""
    parsed: dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            raise ValueError(f"Expected key=value, got {token!r}")
        key, value = token.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key in {token!r}")
        parsed[key] = value
    return parsed


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
        "[dim]Inspect:[/] [cyan]resource describe <name-or-id>[/] · "
        "[dim]Invoke:[/] [cyan]resource invoke <ref> key=value ...[/]"
    )
    return 0


def cmd_resource_invoke(ctx: CliContext, args: list[str]) -> int:
    from rich.panel import Panel

    if not args:
        ctx.console.print(
            "[red]Usage:[/] resource invoke <ref> [key=value ...]\n"
            "[dim]Or:[/] resource invoke --provider <name> --resource-id <id> [key=value ...]"
        )
        return 1

    provider: str | None = None
    resource_id: str | None = None
    action: str | None = None
    resource_ref: str | None = None
    tokens: list[str] = []

    index = 0
    if args[0] == "--provider":
        if len(args) < 3:
            ctx.console.print("[red]Usage:[/] resource invoke --provider <name> --resource-id <id>")
            return 1
        provider = args[1]
        index = 2
        while index < len(args):
            if args[index] == "--resource-id" and index + 1 < len(args):
                resource_id = args[index + 1]
                index += 2
                continue
            if args[index] == "--action" and index + 1 < len(args):
                action = args[index + 1]
                index += 2
                continue
            tokens.append(args[index])
            index += 1
    else:
        resource_ref = args[0]
        tokens = args[1:]

    try:
        state = _parse_key_values(tokens)
    except ValueError as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1

    try:
        result = ctx.app.invoke_resource(
            resource_ref,
            provider=provider,
            action=action,
            resource_id=resource_id,
            state=state,
            params=dict(state),
        )
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1

    if result.success:
        ctx.console.print(
            Panel(
                json.dumps(result.data, indent=2, default=str),
                title="[green]Resource invoke succeeded[/]",
                border_style="green",
            )
        )
        return 0

    ctx.console.print(
        Panel(
            result.error or "invoke failed",
            title="[red]Resource invoke failed[/]",
            border_style="red",
        )
    )
    return 1


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
