"""
Command registry — maps CLI/REPL phrases to command-mode handlers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from palm.runtimes.cli.commands import (
    flow,
    instance,
    process,
    status,
    system,
    wizard,
)
from palm.runtimes.cli.commands import (
    help as help_cmd,
)
from palm.runtimes.cli.commands import (
    input as input_cmd,
)
from palm.runtimes.cli.commands.doctor import run_doctor
from palm.runtimes.cli.shared.context import CliContext

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


def _cmd_doctor(ctx: CliContext, _args: list[str]) -> int:
    return run_doctor(ctx)


def build_registry() -> CommandRegistry:
    reg = CommandRegistry()

    reg.register("help", help_cmd.cmd_help)
    reg.register("doctor", _cmd_doctor)
    reg.register("status", status.cmd_status)
    reg.register("version", system.cmd_version)

    reg.register("process list", process.cmd_process_list)
    reg.register("process submit", process.cmd_process_submit)
    reg.register("process resume", process.cmd_process_resume)

    reg.register("flow list", flow.cmd_flow_list)
    reg.register("flow start", flow.cmd_flow_start)
    reg.register("start", flow.cmd_start)

    reg.register("instance list", instance.cmd_instance_list)
    reg.register("instance snapshots", instance.cmd_instance_snapshots)
    reg.register("instance status", status.cmd_status)
    reg.register("instance resume", process.cmd_process_resume)
    reg.register("instance prune", instance.cmd_instance_prune)

    reg.register("wizard list", wizard.cmd_wizard_list)
    reg.register("wizard start", wizard.cmd_wizard_start)
    reg.register("wizard status", wizard.cmd_wizard_status)
    reg.register("wizard input", wizard.cmd_wizard_input)

    reg.register("input", input_cmd.cmd_input)
    reg.register("back", input_cmd.cmd_back)

    reg.register("sessions", instance.cmd_instance_list)
    reg.register("definitions", process.cmd_process_list)
    reg.register("clear", system.cmd_clear)
    reg.register("exit", system.cmd_exit)
    reg.register("quit", system.cmd_exit)

    return reg
