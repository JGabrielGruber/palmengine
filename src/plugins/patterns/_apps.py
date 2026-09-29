"""
Django-style autoloading for pattern apps.

Each entry in ``INSTALLED_PATTERNS`` names a package that exists.
``autoload`` does not import it. Import the pattern module to register it.
"""

from __future__ import annotations

# Real patterns only — intention stubs listed separately (ST-003 / SD-013).
INSTALLED_PATTERNS: tuple[str, ...] = (
    "dag",
    "parallel",
    "pipeline",
    "wizard",
)

# Not auto-loaded. Purpose in docs/STUBS.md (phase-ticker body must not look installed).
INTENTION_PATTERNS: tuple[str, ...] = ("etl",)


def autoload(names: tuple[str, ...]) -> None:
    """Refuse a catalog import. Import the pattern module that registers the name."""
    if names:
        joined = ", ".join(names)
        raise RuntimeError(
            f"catalog autoload is withdrawn; import the module that registers: {joined}"
        )
