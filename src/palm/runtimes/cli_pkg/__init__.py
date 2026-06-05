"""Modern Palm CLI — Rich output and EmbeddedRuntime commands."""

from palm.runtimes.cli_pkg.bootstrap import bootstrap_runtime, shutdown_context
from palm.runtimes.cli_pkg.repl import run_repl

__all__ = ["bootstrap_runtime", "run_repl", "shutdown_context"]
