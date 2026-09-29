"""
Django-style autoloading for provider apps.
"""

from __future__ import annotations

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
    """Refuse a catalog import. Import the provider module that registers the name."""
    if names:
        joined = ", ".join(names)
        raise RuntimeError(
            f"catalog autoload is withdrawn; import the module that registers: {joined}"
        )
