"""
CLI runtime — command-line and REPL entry point for Palm.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from palm import __version__
from palm.core.registry import pattern_registry, storage_registry
from palm.runtimes.cli_pkg.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli_pkg.commands.registry import build_registry
from palm.runtimes.cli_pkg.repl import run_repl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="palm",
        description="Palm Engine — multi-step transactional workflow orchestration",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Palm {__version__}",
    )
    parser.add_argument(
        "--backend",
        default="memory",
        help="Storage backend name (default: memory)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Optional data directory (definitions under data-dir/definitions)",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    sub.add_parser("repl", help="Interactive REPL (default when no subcommand)")
    status_p = sub.add_parser(
        "status",
        help="Engine status, or instance/job status when instance_id is given",
    )
    status_p.add_argument(
        "instance_id",
        nargs="?",
        default=None,
        help="Process instance id (optional)",
    )

    proc = sub.add_parser("process", help="Process definition commands")
    proc_sub = proc.add_subparsers(dest="process_cmd", required=True)
    proc_sub.add_parser("list", help="List process and flow definitions")
    submit_p = proc_sub.add_parser("submit", help="Submit a process by name or id")
    submit_p.add_argument("ref", help="Process name or definition id")
    resume_p = proc_sub.add_parser("resume", help="Resume a persisted instance")
    resume_p.add_argument("instance_id", help="Process instance id")

    inst = sub.add_parser("instance", help="Process instance commands")
    inst_sub = inst.add_subparsers(dest="instance_cmd", required=True)
    inst_sub.add_parser("list", help="List persisted instances")

    wiz = sub.add_parser("wizard", help="Wizard flow commands")
    wiz_sub = wiz.add_subparsers(dest="wizard_cmd", required=True)
    wiz_sub.add_parser("list", help="List wizard flows")
    start_p = wiz_sub.add_parser("start", help="Start a wizard flow")
    start_p.add_argument("flow", help="Flow name or definition id")

    for name, help_text in (
        ("input", "Provide input to a waiting wizard instance"),
        ("back", "Backtrack to a previous wizard step"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument(
            "args",
            nargs=argparse.REMAINDER,
            help="[<instance_id>] <value> or [<instance_id>] <step_slug>",
        )

    status_inst = sub.add_parser(
        "status-instance",
        help=argparse.SUPPRESS,
    )
    status_inst.add_argument("instance_id", nargs="?", default=None)

    return parser


def _print_engine_status(ctx: object) -> int:
    console = ctx.console  # type: ignore[attr-defined]
    from rich.panel import Panel

    console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            f"Runtime: embedded\n"
            f"Patterns: {', '.join(pattern_registry.names())}\n"
            f"Storage:  {', '.join(storage_registry.names())}",
            title="Status",
            border_style="green",
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point registered in pyproject.toml."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        args.command = "repl"

    ctx = bootstrap_runtime(backend=args.backend, data_dir=args.data_dir)
    registry = build_registry()
    exit_code = 0

    try:
        if args.command == "repl":
            exit_code = run_repl(ctx)
        elif args.command == "status":
            if args.instance_id:
                exit_code = registry.dispatch(ctx, f"status {args.instance_id}")
            else:
                exit_code = _print_engine_status(ctx)
        elif args.command == "process":
            phrase = f"process {args.process_cmd}"
            extra: list[str] = []
            if args.process_cmd == "submit":
                extra = [args.ref]
            elif args.process_cmd == "resume":
                extra = [args.instance_id]
            exit_code = registry.dispatch(ctx, " ".join([phrase, *extra]).strip())
        elif args.command == "instance":
            exit_code = registry.dispatch(ctx, f"instance {args.instance_cmd}")
        elif args.command == "wizard":
            extra = [getattr(args, "flow", "")] if args.wizard_cmd == "start" else []
            exit_code = registry.dispatch(
                ctx, " ".join([f"wizard {args.wizard_cmd}", *extra]).strip()
            )
        elif args.command == "input":
            line = "input " + " ".join(getattr(args, "args", []))
            exit_code = registry.dispatch(ctx, line.strip())
        elif args.command == "back":
            line = "back " + " ".join(getattr(args, "args", []))
            exit_code = registry.dispatch(ctx, line.strip())
        else:
            parser.print_help()
            exit_code = 1
    except EOFError:
        pass
    finally:
        shutdown_context(ctx)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())