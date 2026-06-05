"""
Interactive REPL — prompt_toolkit + Rich, EmbeddedRuntime-backed commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from palm import __version__
from palm.runtimes.cli_pkg.commands.registry import CommandRegistry, build_registry
from palm.runtimes.cli_pkg.context import CliContext


def run_repl(ctx: CliContext, *, history_path: Path | None = None) -> int:
    """Run the interactive REPL until exit."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from rich.panel import Panel
    except ImportError as exc:
        raise SystemExit(
            "REPL requires prompt-toolkit. Install with: uv sync --extra cli"
        ) from exc

    from prompt_toolkit.completion import Completer, Completion

    registry = build_registry()
    completer = _make_completer(registry, Completer, Completion)

    hist = history_path or Path.home() / ".palm" / "history"
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
            "Try [cyan]wizard start onboard[/] or [cyan]process list[/].",
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
    if ctx.active_instance_id:
        short = ctx.active_instance_id[:8]
        return f"palm:{short} ●> "
    return "palm> "


def _make_completer(registry: CommandRegistry, completer_cls: Any, completion_cls: Any) -> Any:
    phrases = sorted(registry.handlers.keys(), key=len)
    tokens = sorted({p.split()[0] for p in phrases})

    class _ReplCompleter(completer_cls):
        def get_completions(self, document: Any, complete_event: Any) -> Any:
            text = document.text_before_cursor.lower()
            words = text.split()

            if len(words) <= 1:
                prefix = text
                for token in tokens:
                    if token.startswith(prefix):
                        yield completion_cls(token, start_position=-len(prefix))
                for phrase in phrases:
                    if phrase.startswith(prefix):
                        yield completion_cls(phrase, start_position=-len(prefix))
                return

            prefix = " ".join(words)
            for phrase in phrases:
                if phrase.startswith(prefix):
                    yield completion_cls(phrase, start_position=-len(prefix))

    return _ReplCompleter()