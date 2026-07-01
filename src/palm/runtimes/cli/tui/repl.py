"""
Interactive REPL — prompt_toolkit + Rich, EmbeddedRuntime-backed commands.
"""

from __future__ import annotations

from pathlib import Path

from palm import __version__
from palm.runtimes.cli.commands.registry import CommandRegistry, build_registry
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.startup import format_persistence_notice
from palm.runtimes.cli.tui.completion import build_repl_completer
from palm.runtimes.cli.tui.prompt import build_repl_prompt


def dispatch_repl_line(ctx: CliContext, registry: CommandRegistry, line: str) -> int:
    """Dispatch one REPL line, routing plain text to assist input when active."""
    if ctx.active_assist_session_id and not registry.matches_command(line):
        return registry.dispatch(ctx, f"assist input {line}")
    return registry.dispatch(ctx, line)


def run_repl(ctx: CliContext, *, history_path: Path | None = None) -> int:
    """Run the interactive REPL until exit."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from rich.panel import Panel
    except ImportError as exc:
        raise SystemExit(
            "REPL requires prompt-toolkit. Install with: pip install palmengine[cli]"
        ) from exc

    from prompt_toolkit.completion import Completer, Completion

    registry = build_registry()
    _ = ctx.repl
    completer = build_repl_completer(
        ctx, registry, completer_cls=Completer, completion_cls=Completion
    )

    hist = history_path or Path.home() / ".palm" / ".history"
    hist.parent.mkdir(parents=True, exist_ok=True)

    session: PromptSession[str] = PromptSession(
        history=FileHistory(str(hist)),
        completer=completer,
        style=Style.from_dict({"prompt": "ansicyan bold"}),
    )

    ctx.console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            "Type [bold]help[/] for commands. "
            "Try [cyan]assist start operator-entry[/] (guided entry), "
            "[cyan]status[/] (dashboard), or [cyan]flow start onboard[/].\n\n"
            f"{format_persistence_notice(ctx.app)}",
            title="🌴 Palm REPL",
            border_style="green",
        )
    )

    while True:
        try:
            line = session.prompt(build_repl_prompt(ctx))
            if not line.strip():
                continue
            dispatch_repl_line(ctx, registry, line)
        except EOFError:
            ctx.console.print("\n[dim]Goodbye.[/]")
            break
        except KeyboardInterrupt:
            ctx.console.print("^C")
            continue
        except Exception as exc:
            ctx.console.print(f"[red bold]Error:[/] {exc}")
    return 0
