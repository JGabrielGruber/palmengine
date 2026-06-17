"""
Command catalog — primary phrases and backward-compatible aliases.

Primary commands route through ApplicationHost + CQRS. Aliases resolve to the
same handlers for REPL and one-shot use.
"""

from __future__ import annotations

# REPL / registry aliases → canonical phrase (longest-match registration order
# is handled separately in :mod:`palm.runtimes.cli.commands.registry`).
COMMAND_ALIASES: dict[str, str] = {
    "start": "flow start",
    "definitions": "process list",
    "sessions": "instance list",
    "instance status": "status",
    "wizard status": "status",
    "wizard input": "input",
    "process resume": "instance resume",
}
