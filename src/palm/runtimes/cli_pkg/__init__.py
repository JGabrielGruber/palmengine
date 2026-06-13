"""Backward-compatible re-export — prefer ``palm.runtimes.cli.pkg``."""

from palm.runtimes.cli.pkg import bootstrap_runtime, run_repl, shutdown_context

__all__ = ["bootstrap_runtime", "run_repl", "shutdown_context"]
