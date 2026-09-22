"""
Command catalog — canonical aliases.

Primary commands route through ApplicationHost + CQRS. One alias remains for
ergonomics: ``start`` → ``flow start``. Legacy phrase aliases have been
removed (SU-005).
"""

from __future__ import annotations

# REPL aliases → canonical phrase (longest-match registration order
# is handled separately in :mod:`palm.runtimes.cli.commands.registry`).
COMMAND_ALIASES: dict[str, str] = {
    "start": "flow start",
}
