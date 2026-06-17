"""Status commands — re-export diagnostics entry points."""

from __future__ import annotations

from palm.runtimes.cli.commands.diagnostics import cmd_status, run_engine_brief

# Backward-compatible alias used by older imports.
cmd_engine_status = run_engine_brief

__all__ = ["cmd_status", "cmd_engine_status", "run_engine_brief"]
