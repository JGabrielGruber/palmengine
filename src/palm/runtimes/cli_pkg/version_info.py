"""
Version reporting for the Palm CLI.
"""

from __future__ import annotations

import platform
import sys
from typing import Any

from palm import __version__


def print_version_brief() -> None:
    """Print a single-line version string (no Rich required)."""
    print(f"Palm {__version__}")


def print_version_full(console: Any | None = None) -> int:
    """
    Print build metadata and registered plugin names.

    Does not start ``EmbeddedRuntime`` — safe for CI and quick checks.
    """
    import palm.patterns
    import palm.providers
    import palm.storages  # noqa: F401
    from palm.core.registry import pattern_registry, provider_registry, storage_registry

    lines = [
        f"Palm Engine {__version__}",
        f"Python {sys.version.split()[0]} on {platform.system()} {platform.release()}",
        f"Patterns:  {', '.join(sorted(pattern_registry.names()))}",
        f"Providers: {', '.join(sorted(provider_registry.names()))}",
        f"Storage:   {', '.join(sorted(storage_registry.names()))}",
        "",
        "Quick start:",
        "  palm doctor              # health + examples",
        "  palm repl                # interactive shell",
        "  palm wizard start onboard",
        "  python examples/full_demo.py",
    ]

    if console is None:
        for line in lines:
            print(line)
        return 0

    from rich.panel import Panel

    console.print(
        Panel(
            "\n".join(lines),
            title="🌴 Palm",
            subtitle="https://github.com/JGabrielGruber/palmengine",
            border_style="cyan",
        )
    )
    return 0
