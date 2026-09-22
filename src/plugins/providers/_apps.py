"""
Django-style autoloading for provider apps.
"""

from __future__ import annotations

import importlib

# Real capabilities only — intention stubs listed separately (ST-001 / SD-013).
INSTALLED_PROVIDERS: tuple[str, ...] = (
    "rest",
    "palm",
    "kv",
    "file",
    "authoring",
    # neonroot removed 0.56 — isolation is WorkloadRuntime under palm.runners.neonroot
)

# Not auto-loaded. Purpose lives in docs/STUBS.md; packages may still exist for future work.
INTENTION_PROVIDERS: tuple[str, ...] = (
    "graphql",
    "postgres",
)


def autoload(names: tuple[str, ...]) -> None:
    """Import the named provider apps (triggers registry side effects)."""
    for name in names:
        importlib.import_module(f"plugins.providers.{name}")
