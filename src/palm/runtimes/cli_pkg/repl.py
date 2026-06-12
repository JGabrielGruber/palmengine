"""
Interactive REPL — prompt_toolkit + Rich, EmbeddedRuntime-backed commands.
"""

from __future__ import annotations

from pathlib import Path

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
        raise SystemExit(
            "REPL requires prompt-toolkit. Install with: pip install palmengine[cli]"
        ) from exc

    from prompt_toolkit.completion import Completer, Completion

    from palm.runtimes.cli_pkg.completion import build_repl_completer

    registry = build_registry()
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

    from palm.runtimes.cli_pkg.startup import format_persistence_notice

    ctx.console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            "Type [bold]help[/] for commands. "
            "Try [cyan]wizard start onboard[/], [cyan]wizard start parallel-demo[/], "
            "or [cyan]process list[/].\n\n"
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

    try:
        from palm.runtimes.cli_pkg.job_context import inspect_job

        job = ctx.job_for_instance(ctx.active_instance_id)
        context = inspect_job(job)

        flow = None
        for summary in ctx.list_instance_summaries():
            if summary.instance_id == ctx.active_instance_id:
                flow = summary.flow_name or summary.process_name
                break

        if flow and context.step:
            suffix = f" {flow}:{context.step}"
        elif flow:
            suffix = f" {flow}"

        scope_suffix = context.repl_scope_suffix
        if scope_suffix and scope_suffix not in suffix:
            suffix = f"{suffix}{scope_suffix}"

        if context.branch_progress and context.pattern == "parallel":
            suffix = f"{suffix} [{context.branch_progress}]"

        if context.validation_error:
            preview = (
                context.validation_error
                if len(context.validation_error) <= 20
                else f"{context.validation_error[:17]}…"
            )
            suffix = f"{suffix} !{preview}"
    except Exception:
        pass

    return f"palm:{short}{suffix} ●> "