"""
Interactive REPL for Palm Solid Admin CLI.

Built with prompt_toolkit for excellent UX (history, completion, multiline).
Uses Rich for beautiful output.
"""

from __future__ import annotations

import shlex
from collections.abc import Callable
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from palm.cli.solid.legacy.orchestrator import Orchestrator
from palm.cli.solid.legacy.wizard.engine import WizardEngine
from palm.config.settings import settings
from palm.exceptions import PalmError
from palm.utils.logging import logger


class PalmCommandCompleter(Completer):
    """
    Context-aware dynamic completer for the Palm REPL (0.1.1).

    Supports:
    - Top-level commands
    - Wizard IDs after "wizard start"
    - Session IDs for status/input/back when active sessions exist
    - Step slugs for "back <session> <slug>" using the session's allowed back steps
    """

    BASE_COMMANDS = [
        "help",
        "wizard list",
        "wizard start",
        "wizard status",
        "wizard input",
        "back",
        "ps",
        "sessions",
        "clear",
        "exit",
        "quit",
    ]

    def __init__(
        self,
        engine: WizardEngine,
        get_active_session_id: Callable[[], str | None],
    ) -> None:
        self.engine = engine
        self.get_active_session_id = get_active_session_id

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        text_lower = text.lower().strip()
        words = text_lower.split()

        # Top-level command completion
        if len(words) <= 1:
            prefix = text_lower
            for cmd in self.BASE_COMMANDS:
                if cmd.startswith(prefix):
                    yield Completion(cmd, start_position=-len(prefix))
            return

        first = words[0]
        second = words[1] if len(words) > 1 else ""

        # wizard start <wizard_id>
        if first == "wizard" and second == "start":
            prefix = words[2] if len(words) > 2 else ""
            for wiz in self.engine.list_wizards():
                wid = wiz["id"]
                if wid.lower().startswith(prefix):
                    yield Completion(wid, start_position=-len(prefix))
            return

        # Commands that accept session_id as next argument
        if first in ("wizard", "back") and second in ("status", "input", "back"):
            # "wizard status", "wizard input", "back"
            prefix = words[2] if len(words) > 2 else ""
            active = self.get_active_session_id()
            candidates: list[str] = []

            # Prefer active session first
            if active:
                candidates.append(active)

            # Add other active sessions
            for s in self.engine.store.list_active():
                if s.id not in candidates:
                    candidates.append(s.id)

            for sid in candidates:
                if sid.lower().startswith(prefix):
                    yield Completion(sid, start_position=-len(prefix))
            return

        # back <session_id> <step_slug>
        if first == "back" and len(words) >= 2:
            # words[1] is the session id (or being typed)
            if len(words) == 2:
                # still completing session id
                prefix = words[1]
                for s in self.engine.store.list_active():
                    if s.id.lower().startswith(prefix):
                        yield Completion(s.id, start_position=-len(prefix))
                return

            # Completing step slug for a specific session
            session_id = words[1]
            prefix = words[2] if len(words) > 2 else ""

            try:
                sess = self.engine.store.get(session_id)
                if sess and sess.back_stack:
                    for slug in sess.back_stack:
                        if slug.lower().startswith(prefix):
                            yield Completion(slug, start_position=-len(prefix))
            except Exception:
                pass
            return

        # wizard input <session> <value>  -> we don't complete the value, but we can help with session
        if first == "wizard" and second == "input" and len(words) <= 3:
            prefix = words[2] if len(words) > 2 else ""
            active = self.get_active_session_id()
            for s in self.engine.store.list_active():
                sid = s.id
                if sid == active:
                    sid = f"{sid}  # active"
                if sid.lower().startswith(prefix):
                    yield Completion(s.id, start_position=-len(prefix))
            return

        # Fallback: still offer base commands
        for cmd in self.BASE_COMMANDS:
            if cmd.startswith(text_lower):
                yield Completion(cmd, start_position=-len(text_lower))


class PalmREPL:
    """
    Interactive Solid Admin REPL for Palm (major UX improvements in 0.1.1).

    Features:
    - Context-aware tab completion (wizards, sessions, backtrackable steps)
    - Active session memory (most commands default to the last started session)
    - Beautiful Rich rendering with explicit "Available Actions" guidance
    - Smart argument parsing for `wizard input` and `back`
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        engine: WizardEngine,
        console: Console,
    ) -> None:
        self.orchestrator = orchestrator
        self.engine = engine
        self.console = console

        self.active_session_id: str | None = None  # convenience for quick input + autocomplete

        # Create context-aware completer (0.1.1)
        completer = PalmCommandCompleter(
            engine=engine,
            get_active_session_id=lambda: self.active_session_id,
        )

        self.session: PromptSession[str] = PromptSession(
            history=FileHistory(str(settings.resolved_history_file)),
            completer=completer,
            style=Style.from_dict(
                {
                    "prompt": "ansicyan bold",
                }
            ),
            multiline=False,
        )

        self.commands: dict[str, Any] = {
            "help": self.cmd_help,
            "wizard list": self.cmd_wizard_list,
            "wizard start": self.cmd_wizard_start,
            "wizard status": self.cmd_wizard_status,
            "wizard input": self.cmd_wizard_input,
            "back": self.cmd_back,
            "ps": self.cmd_ps,
            "sessions": self.cmd_sessions,
            "clear": self.cmd_clear,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }

    def run(self) -> None:
        while True:
            try:
                text = self.session.prompt(self._get_prompt())
                if not text.strip():
                    continue
                self._dispatch(text.strip())
            except EOFError:
                self.console.print("\n[dim]Goodbye.[/]")
                break
            except KeyboardInterrupt:
                self.console.print("^C")
                continue
            except PalmError as e:
                # 0.1.1: clearer, actionable error messages
                if "validation" in str(e).lower():
                    self.console.print(f"[red]Validation failed:[/] {e}")
                    self.console.print(
                        "[dim]Hint: Use 'back <slug>' to correct previous answers.[/]"
                    )
                else:
                    self.console.print(f"[red]Error:[/] {e}")
            except Exception as e:
                self.console.print(f"[red bold]Unexpected error:[/] {e}")
                logger.exception("Unexpected REPL error")

    def _get_prompt(self) -> str:
        if self.active_session_id:
            short = self.active_session_id[:8]
            return f"[palm:{short} ●]> "
        return settings.cli_prompt

    def _dispatch(self, line: str) -> None:
        parts = shlex.split(line)
        if not parts:
            return

        cmd = parts[0]
        args = parts[1:]

        # Two-word commands
        if len(parts) >= 2:
            two_word = f"{parts[0]} {parts[1]}"
            if two_word in self.commands:
                self.commands[two_word](args[1:] if len(args) > 1 else [])
                return

        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            self.console.print(f"[yellow]Unknown command:[/] {cmd}. Type [bold]help[/].")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def cmd_help(self, args: list[str]) -> None:
        help_text = """
[bold cyan]Palm Solid Admin CLI Commands[/]

[bold]Wizard Management[/]
  wizard list                     List all registered wizards
  wizard start <wizard_id>        Start a new wizard session
  wizard status [session_id]      Show status (uses active if omitted)
  wizard input <session_id> <val> Submit input to a session

[bold]Session Control[/]
  back <session_id> <step_slug>   Backtrack a session to a previous step
  sessions                        List active/persisted sessions

[bold]System[/]
  ps                              Show running processes (ProcessManager)
  clear                           Clear the screen
  help                            This message
  exit / quit                     Leave the REPL

[bold]Tips (0.1.1)[/]
  • After starting a wizard, the session becomes [bold]active[/] (shown in prompt as [cyan]palm:xxxxxx ●[/]).
  • Many commands now default to the active session:
      wizard input <value>
      wizard status
      back <step-slug>
  • Tab completion is now dynamic (wizards, sessions, step slugs).
  • On summary/commit steps you can usually just type [green]confirm[/] or [green]yes[/].
"""
        self.console.print(Panel(help_text.strip(), title="Help", border_style="cyan"))

    def cmd_wizard_list(self, args: list[str]) -> None:
        wizards = self.engine.list_wizards()
        if not wizards:
            self.console.print("[yellow]No wizards registered.[/]")
            return

        table = Table(title="Registered Wizards", show_lines=True)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Version", style="dim")
        table.add_column("Steps", justify="right")
        table.add_column("Description", style="white")

        for w in wizards:
            table.add_row(
                w["id"],
                w["name"],
                w["version"],
                str(w["step_count"]),
                w["description"][:60] + ("..." if len(w["description"]) > 60 else ""),
            )
        self.console.print(table)

    def cmd_wizard_start(self, args: list[str]) -> None:
        if not args:
            self.console.print("[red]Usage:[/] wizard start <wizard_id>")
            return

        wizard_id = args[0]
        try:
            session, ctx = self.engine.start_session(wizard_id)
            self.active_session_id = session.id
            self._render_context(ctx)
            self.console.print(f"\n[dim]Session ID:[/] [bold]{session.id}[/] (now active)")
        except PalmError as e:
            self.console.print(f"[red]Failed to start wizard:[/] {e}")

    def cmd_wizard_status(self, args: list[str]) -> None:
        # 0.1.1: defaults to active session
        sid = args[0] if args else self.active_session_id
        if not sid:
            self.console.print("[red]No session id provided and no active session.[/]")
            return
        try:
            status = self.engine.get_status(sid)
            table = Table(title=f"Session {sid[:12]}...", show_header=False)
            for k, v in status.items():
                table.add_row(f"[bold]{k}[/]", str(v))
            self.console.print(table)
        except PalmError as e:
            self.console.print(f"[red]{e}[/]")

    def cmd_wizard_input(self, args: list[str]) -> None:
        """
        0.1.1: Supports:
          wizard input <value...>          (uses active session)
          wizard input <session_id> <value...>
        """
        if not args:
            self.console.print("[red]Usage:[/] wizard input [<session_id>] <value>")
            return

        # Smart default to active session
        if len(args) == 1 and self.active_session_id:
            sid = self.active_session_id
            value = args[0]
        elif len(args) >= 2:
            sid = args[0]
            value = " ".join(args[1:])
        else:
            self.console.print("[red]Usage:[/] wizard input [<session_id>] <value>")
            return

        try:
            ctx = self.engine.process_input(sid, value)
            self._render_context(ctx)
            if ctx.status.value == "committed":
                self.active_session_id = None
                logger.info(f"Session {sid[:8]} committed via CLI")
        except PalmError as e:
            self.console.print(f"[red]Input error:[/] {e}")
            # Try to re-show context for the session the user was talking to
            try:
                status = self.engine.get_status(sid)
                self.console.print(f"[dim]Current step: {status.get('current_step')}[/]")
            except Exception:
                pass

    def cmd_back(self, args: list[str]) -> None:
        """
        0.1.1 UX improvement:
          back <step_slug>                 (uses active session)
          back <session_id> <step_slug>
        """
        if not args:
            self.console.print("[red]Usage:[/] back [<session_id>] <step_slug>")
            return

        if len(args) == 1 and self.active_session_id:
            sid = self.active_session_id
            target = args[0]
        elif len(args) >= 2:
            sid, target = args[0], args[1]
        else:
            self.console.print("[red]Usage:[/] back [<session_id>] <step_slug>")
            return

        try:
            ctx = self.engine.backtrack(sid, target)
            self._render_context(ctx)
            self.console.print(f"[green]Backtracked to[/] [bold]{target}[/]")
        except PalmError as e:
            self.console.print(f"[red]{e}[/]")

    def cmd_ps(self, args: list[str]) -> None:
        procs = self.orchestrator.process_manager.list()
        if not procs:
            self.console.print("[dim]No managed processes currently running.[/]")
            return
        table = Table(title="Managed Processes")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("OS PID")
        table.add_column("Alive")
        table.add_column("Status")
        for p in procs:
            table.add_row(
                p["id"][:20],
                p["name"],
                str(p["os_pid"]),
                "✓" if p["alive"] else "✗",
                p["status"],
            )
        self.console.print(table)

    def cmd_sessions(self, args: list[str]) -> None:
        sessions = self.orchestrator.store.list_active()
        if not sessions:
            self.console.print("[dim]No active sessions.[/]")
            return

        table = Table(title="Active Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Wizard")
        table.add_column("Status", style="yellow")
        table.add_column("Step")
        table.add_column("Last Activity")

        for s in sessions:
            table.add_row(
                s.id[:12],
                s.wizard_id,
                s.status.value,
                s.current_step_slug or "-",
                s.last_activity_at.strftime("%H:%M:%S"),
            )
        self.console.print(table)

    def cmd_clear(self, args: list[str]) -> None:
        self.console.clear()

    def cmd_exit(self, args: list[str]) -> None:
        self.console.print("[dim]Shutting down...[/]")
        self.orchestrator.shutdown()
        raise EOFError()

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _render_context(self, ctx: Any) -> None:
        """
        0.1.1: Significantly improved rendering with explicit action guidance.
        """
        title = f"[bold]{ctx.wizard_name}[/] — [cyan]{ctx.current_step_slug}[/] ({ctx.current_step_type})"

        body = f"[bold]{ctx.prompt}[/]\n"
        if ctx.guidelines:
            body += f"\n[dim]{ctx.guidelines}[/]\n"

        # Show suggested input prominently for confirmation-style steps
        if ctx.suggested_input:
            body += f"\n[yellow]→ Suggested:[/] [bold]{ctx.suggested_input}[/]\n"

        if ctx.choices:
            body += "\n[bold]Choices:[/]\n"
            for c in ctx.choices:
                val = c.get("value", c)
                label = c.get("label", val)
                body += f"  • [green]{val}[/]: {label}\n"

        # New prominent "Available Actions" section (the key 0.1.1 UX win)
        if ctx.available_actions:
            body += "\n[bold cyan]Available Actions:[/]\n"
            for action in ctx.available_actions:
                body += f"  • {action}\n"

        if ctx.allowed_back_steps:
            body += f"\n[dim]Back steps: {' | '.join(ctx.allowed_back_steps)}[/]"

        if ctx.collected_data:
            body += "\n\n[dim]Collected so far:[/]\n"
            for k, v in list(ctx.collected_data.items())[:6]:
                if not k.startswith("__"):
                    body += f"  {k}: [white]{v}[/]\n"

        panel = Panel(
            body.strip(),
            title=title,
            border_style="blue",
            subtitle=f"Session: {ctx.session_id[:8]}  |  Status: {ctx.status}",
        )
        self.console.print(panel)

        # Extra emphasis on terminal steps
        if ctx.current_step_type in ("summary", "commit"):
            self.console.print(
                "[bold yellow]Type[/] [bold green]confirm[/] [bold yellow]or[/] [bold green]yes[/] [bold yellow]to continue.[/]"
            )

        if ctx.status.value == "committed":
            self.console.print(
                Panel(
                    f"[bold green]✓ Wizard completed successfully![/]\n\n"
                    f"Result: {ctx.metadata.get('commit_result', {})}",
                    border_style="green",
                )
            )
