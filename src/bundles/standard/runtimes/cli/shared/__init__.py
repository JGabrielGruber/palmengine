"""Shared CLI infrastructure — session, parsing, and mode-agnostic helpers."""

from bundles.standard.runtimes.cli.shared.bootstrap import bootstrap_runtime, shutdown_context
from bundles.standard.runtimes.cli.shared.context import CliContext

__all__ = ["CliContext", "bootstrap_runtime", "shutdown_context"]
