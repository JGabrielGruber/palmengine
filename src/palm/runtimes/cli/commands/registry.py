"""
Command registry — maps CLI/REPL phrases to command-mode handlers.

Primary commands use ApplicationHost + CQRS. Legacy aliases remain registered
for backward compatibility (see :mod:`palm.runtimes.cli.commands.catalog`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from palm.runtimes.cli.commands import (
    assist,
    diagnostics,
    flow,
    instance,
    process,
    resource,
    system,
    wizard,
)
from palm.runtimes.cli.commands import (
    help as help_cmd,
)
from palm.runtimes.cli.commands import (
    input as input_cmd,
)
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

    def matches_command(self, line: str) -> bool:
        """Return True when ``line`` begins with a registered command phrase."""
        import shlex

        parts = shlex.split(line.strip())
        if not parts:
            return False
        for width in range(min(3, len(parts)), 0, -1):
            if " ".join(parts[:width]) in self.handlers:
                return True
        return False


def build_registry() -> CommandRegistry:
    reg = CommandRegistry()

    # System
    reg.register("help", help_cmd.cmd_help)
    reg.register("version", system.cmd_version)
    reg.register("clear", system.cmd_clear)
    reg.register("exit", system.cmd_exit)
    reg.register("quit", system.cmd_exit)

    # Host diagnostics (CQRS read models + dashboard)
    reg.register("status", diagnostics.cmd_status)
    reg.register("doctor", diagnostics.cmd_doctor)

    # Assist (host.assist — conversational operator guidance)
    reg.register("assist list", assist.cmd_assist_list)
    reg.register("assist start", assist.cmd_assist_start)
    reg.register("assist input", assist.cmd_assist_input)
    reg.register("assist handoff", assist.cmd_assist_handoff)
    reg.register("assist status", assist.cmd_assist_status)
    reg.register("assist cancel", assist.cmd_assist_cancel)

    # Flows (host.submit_flow)
    reg.register("flow list", flow.cmd_flow_list)
    reg.register("flow start", flow.cmd_flow_start)
    reg.register("start", flow.cmd_start)

    # Definitions & multi-flow processes
    reg.register("process list", process.cmd_process_list)
    reg.register("process submit", process.cmd_process_submit)

    # Resource definitions (0.12 Phase 1)
    reg.register("resource list", resource.cmd_resource_list)
    reg.register("resource describe", resource.cmd_resource_describe)
    reg.register("resource invoke", resource.cmd_resource_invoke)

    # Instances (host queries + resume command)
    reg.register("instance list", instance.cmd_instance_list)
    reg.register("instance resume", instance.cmd_instance_resume)
    reg.register("instance snapshots", instance.cmd_instance_snapshots)
    reg.register("instance prune", instance.cmd_instance_prune)

    # Interactive writes (host.provide_input / resume)
    reg.register("input", input_cmd.cmd_input)
    reg.register("back", input_cmd.cmd_back)

    # Legacy aliases — same handlers, shorter phrases
    reg.register("definitions", process.cmd_process_list)
    reg.register("sessions", instance.cmd_instance_list)
    reg.register("instance status", diagnostics.cmd_status)
    reg.register("process resume", instance.cmd_instance_resume)
    reg.register("wizard list", wizard.cmd_wizard_list)
    reg.register("wizard start", wizard.cmd_wizard_start)
    reg.register("wizard status", diagnostics.cmd_status)
    reg.register("wizard input", input_cmd.cmd_input)

    return reg
