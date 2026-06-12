"""
CLI runtime — command-line and REPL entry point for Palm.

Run ``palm --help`` for commands. Use ``palm version --full`` for build and
plugin details without starting the embedded runtime.
"""

from __future__ import annotations

import sys

from palm.app.session import create_console
from palm.runtimes.cli_pkg.args import build_parser, invocation_from_namespace
from palm.runtimes.cli_pkg.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli_pkg.commands.registry import build_registry
from palm.runtimes.cli_pkg.repl import run_repl
from palm.runtimes.cli_pkg.version_info import print_version_brief, print_version_full


def main(argv: list[str] | None = None) -> int:
    """CLI entry point registered in ``pyproject.toml`` as the ``palm`` script."""
    parser = build_parser()
    args = parser.parse_args(argv)
    inv = invocation_from_namespace(args)

    if inv.command == "version":
        if inv.full:
            try:
                return print_version_full(create_console())
            except SystemExit:
                return print_version_full()
        print_version_brief()
        return 0

    if inv.command is None:
        inv.command = "repl"

    show_banner = inv.command not in ("repl", "doctor")
    ctx = bootstrap_runtime(invocation=inv, show_banner=show_banner)
    registry = build_registry()
    exit_code = 0

    try:
        if inv.command == "repl":
            exit_code = run_repl(ctx)
        elif inv.command == "doctor":
            exit_code = registry.dispatch(ctx, "doctor")
        elif inv.command == "status":
            if inv.full:
                exit_code = registry.dispatch(ctx, "doctor")
            elif inv.instance_id:
                exit_code = registry.dispatch(ctx, f"status {inv.instance_id}")
            else:
                exit_code = registry.dispatch(ctx, "status")
        elif inv.command == "process":
            phrase = f"process {inv.process_cmd}"
            extra: list[str] = []
            if inv.process_cmd == "submit" and inv.ref:
                extra = [inv.ref]
            elif inv.process_cmd == "resume" and inv.instance_id:
                extra = [inv.instance_id]
            exit_code = registry.dispatch(ctx, " ".join([phrase, *extra]).strip())
        elif inv.command == "instance":
            if inv.instance_cmd == "list":
                extra = _instance_list_argv(inv)
                exit_code = registry.dispatch(ctx, " ".join(["instance list", *extra]).strip())
            elif inv.instance_cmd == "status":
                ref = inv.instance_id or ""
                exit_code = registry.dispatch(ctx, f"instance status {ref}".strip())
            elif inv.instance_cmd == "snapshots" and inv.instance_id:
                exit_code = registry.dispatch(ctx, f"instance snapshots {inv.instance_id}")
            elif inv.instance_cmd == "resume" and inv.instance_id:
                exit_code = registry.dispatch(ctx, f"instance resume {inv.instance_id}")
            elif inv.instance_cmd == "prune":
                extra = ["--dry-run"] if inv.prune_dry_run else []
                exit_code = registry.dispatch(ctx, " ".join(["instance prune", *extra]).strip())
            else:
                exit_code = 1
        elif inv.command == "flow":
            extra = [inv.flow] if inv.flow_cmd == "start" and inv.flow else []
            exit_code = registry.dispatch(ctx, " ".join([f"flow {inv.flow_cmd}", *extra]).strip())
        elif inv.command == "start" and inv.flow:
            exit_code = registry.dispatch(ctx, f"start {inv.flow}")
        elif inv.command == "wizard":
            extra = [inv.flow] if inv.wizard_cmd == "start" and inv.flow else []
            exit_code = registry.dispatch(
                ctx, " ".join([f"wizard {inv.wizard_cmd}", *extra]).strip()
            )
        elif inv.command == "input":
            line = "input " + " ".join(inv.input_args or [])
            exit_code = registry.dispatch(ctx, line.strip())
        elif inv.command == "back":
            line = "back " + " ".join(inv.input_args or [])
            exit_code = registry.dispatch(ctx, line.strip())
        else:
            parser.print_help()
            exit_code = 1
    except EOFError:
        pass
    finally:
        shutdown_context(ctx)

    return exit_code


def _instance_list_argv(inv: object) -> list[str]:
    argv: list[str] = []
    if getattr(inv, "instance_list_all", False):
        argv.append("--all")
    if getattr(inv, "instance_status", None):
        argv.extend(["--status", str(inv.instance_status)])
    if getattr(inv, "instance_flow", None):
        argv.extend(["--flow", str(inv.instance_flow)])
    if getattr(inv, "instance_limit", None):
        argv.extend(["--limit", str(inv.instance_limit)])
    if getattr(inv, "output_format", "table") == "json":
        argv.append("--format")
        argv.append("json")
    return argv


if __name__ == "__main__":
    sys.exit(main())
