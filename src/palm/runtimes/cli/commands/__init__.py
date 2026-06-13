"""Command-mode handlers — one-shot CLI and REPL phrase dispatch."""

from palm.runtimes.cli.commands.registry import CommandRegistry, build_registry

__all__ = ["CommandRegistry", "build_registry"]