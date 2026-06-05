"""
CLI runtime — interactive command-line entry point for Palm.

This is the primary user-facing runtime today. It wires the embedded runtime
and prints a placeholder banner until full REPL functionality is rebuilt.
"""

from __future__ import annotations

import argparse
import sys

from palm import __version__
from palm.core.registry import pattern_registry, storage_registry
from palm.runtimes.embedded import EmbeddedRuntime


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
        "command",
        nargs="?",
        default="status",
        choices=["status", "version"],
        help="Command to run (default: status)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point registered in pyproject.toml."""
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(f"Palm {__version__}")
        return 0

    runtime = EmbeddedRuntime()
    runtime.start()
    try:
        print(f"🌴 Palm Engine v{__version__}")
        print("Runtime: embedded (placeholder CLI)")
        print("Status: ready — core engines initialized")
        print(f"Patterns: {', '.join(pattern_registry.names())}")
        print(f"Storage:  {', '.join(storage_registry.names())}")
    finally:
        runtime.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
