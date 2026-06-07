"""
Execution runtimes — surfaces that host Palm engines.

- ``embedded`` — in-process library runtime
- ``daemon`` — long-lived background host
- ``cli`` — command-line interface (entry point)
- ``server`` — network host (future)
"""

from palm.runtimes.cli import main
from palm.runtimes.daemon import DaemonRuntime, run_daemon
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.host import RuntimeHost

__all__ = ["DaemonRuntime", "EmbeddedRuntime", "RuntimeHost", "main", "run_daemon"]
