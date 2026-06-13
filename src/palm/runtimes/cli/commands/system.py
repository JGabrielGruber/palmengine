"""System commands — version, screen clear, REPL exit."""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.version_info import print_version_brief, print_version_full


def cmd_version(ctx: CliContext, args: list[str]) -> int:
    if args and args[0] == "--full":
        return print_version_full(ctx.console)
    print_version_brief()
    return 0


def cmd_clear(ctx: CliContext, _args: list[str]) -> int:
    ctx.console.clear()
    return 0


def cmd_exit(_ctx: CliContext, _args: list[str]) -> int:
    raise EOFError()