"""
CLI runtime — command-line and REPL entry point for Palm.

Run ``palm --help`` for commands. Use ``palm version --full`` for build and
plugin details without starting the embedded runtime.
"""

from __future__ import annotations

import sys

from palm.app import HostProfile, run_host
from palm.app.session import create_console
from palm.runtimes.cli.commands.registry import build_registry
from palm.runtimes.cli.shared.args import CliInvocation, build_parser, invocation_from_namespace
from palm.runtimes.cli.shared.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli.shared.dispatch import dispatch_invocation
from palm.runtimes.cli.shared.version_info import print_version_brief, print_version_full
from palm.runtimes.cli.tui.repl import run_repl


def main(argv: list[str] | None = None) -> int:
    """CLI entry point registered in ``pyproject.toml`` as the ``palm`` script."""
    parser = build_parser()
    args = parser.parse_args(argv)
    inv = invocation_from_namespace(args)

    if inv.command == "host":
        from palm.runtimes.cli.shared.args import settings_from_invocation

        settings = settings_from_invocation(inv)
        profile = _host_profile_from_invocation(inv)
        run_host(profile, settings=settings)
        return 0

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

    show_banner = inv.command not in ("repl", "doctor", "status")
    ctx = bootstrap_runtime(invocation=inv, show_banner=show_banner)
    registry = build_registry()
    exit_code = 0

    try:
        if inv.command == "repl":
            exit_code = run_repl(ctx)
        else:
            exit_code = dispatch_invocation(ctx, registry, inv)
    except EOFError:
        pass
    finally:
        shutdown_context(ctx)

    return exit_code


def _host_profile_from_invocation(inv: CliInvocation) -> HostProfile:
    cmd = (inv.host_cmd or "all-in-one").replace("-", "_")
    if cmd in {"all_in_one", "allinone"}:
        return HostProfile.all_in_one()
    if cmd == "master":
        return HostProfile.master_only()
    if cmd == "worker":
        count = inv.host_workers if inv.host_workers is not None else 1
        return HostProfile.worker_only(count=count)
    if cmd == "server":
        return HostProfile.server_only(
            host=inv.host_bind or "127.0.0.1",
            port=inv.host_port or 8080,
        )
    raise ValueError(f"Unknown host subcommand: {inv.host_cmd!r}")


if __name__ == "__main__":
    sys.exit(main())
