"""Command-mode handlers — one-shot CLI and REPL phrase dispatch."""

from bundles.standard.runtimes.cli.commands.registry import CommandRegistry, build_registry

__all__ = ["CommandRegistry", "build_registry"]
