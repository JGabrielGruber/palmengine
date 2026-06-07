"""
Execution runtimes — surfaces that host Palm engines.

- ``embedded`` — in-process library runtime
- ``cli`` — command-line interface (entry point)
- ``server`` — network host (future)
- ``daemon`` — background service (future)
"""

from palm.runtimes.cli import main
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.host import RuntimeHost

__all__ = ["EmbeddedRuntime", "RuntimeHost", "main"]
