"""
Interactive REPL — prompt_toolkit + Rich, EmbeddedRuntime-backed commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm import __version__
from palm.runtimes.cli_pkg.commands.registry import build_registry
from palm.runtimes.cli_pkg.context import CliContext


def run_repl(ctx: CliContext, *, history_path: Path | None = None) -> int:
    """Run the interactive REPL until exit."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from rich.panel import Panel
    except ImportError as exc:
        raise SystemExit("REPL requires prompt-toolkit. Install with: uv sync --extra cli") from exc

    from prompt_toolkit.completion import Completer, Completion

    from palm.runtimes.cli_pkg.completion import build_repl_completer

    registry = build_registry()
    completer = build_repl_completer(ctx, registry, completer_cls=Completer, completion_cls=Completion)

    hist = history_path or Path.home() / ".palm" / "history"
    hist.parent.mkdir(parents=True, exist_ok=True)

    session: PromptSession[str] = PromptSession(
        history=FileHistory(str(hist)),
        completer=completer,
        style=Style.from_dict({"prompt": "ansicyan bold"}),
    )

    from palm.runtimes.cli_pkg.startup import format_persistence_notice

    ctx.console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            "Type [bold]help[/] for commands. "
            "Try [cyan]wizard start onboard[/] or [cyan]process list[/].\n\n"
            f"{format_persistence_notice(ctx.app)}",
            title="🌴 Palm REPL",
            border_style="green",
        )
    )

    while True:
        try:
            line = session.prompt(_prompt(ctx))
            if not line.strip():
                continue
            registry.dispatch(ctx, line)
        except EOFError:
            ctx.console.print("\n[dim]Goodbye.[/]")
            break
        except KeyboardInterrupt:
            ctx.console.print("^C")
            continue
        except Exception as exc:
            ctx.console.print(f"[red bold]Error:[/] {exc}")
    return 0


def _prompt(ctx: CliContext) -> str:
    if not ctx.active_instance_id:
        return "palm> "

    short = ctx.active_instance_id[:8]
    suffix = ""
    for summary in ctx.list_instance_summaries():
        if summary.instance_id == ctx.active_instance_id:
            flow = summary.flow_name or summary.process_name
            step = summary.wizard_step_slug
            if flow and step:
                suffix = f" {flow}:{step}"
            elif flow:
                suffix = f" {flow}"
            break
    return f"palm:{short}{suffix} ●> "
