"""Backward-compatible re-exports — prefer ``palm.runtimes.cli.shared`` and ``.tui``."""

from palm.runtimes.cli.shared import bootstrap_runtime, shutdown_context
from palm.runtimes.cli.tui.repl import run_repl

__all__ = ["bootstrap_runtime", "run_repl", "shutdown_context"]