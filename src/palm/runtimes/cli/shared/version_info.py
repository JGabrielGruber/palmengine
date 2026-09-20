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
    from palm.core.registry import pattern_registry, provider_registry, storage_registry
    from palm.patterns import autoload as autoload_patterns
    from palm.providers import autoload as autoload_providers
    from palm.storages import autoload as autoload_storages

    autoload_patterns()
    autoload_providers()
    autoload_storages()

    lines = [
        f"Palm Engine {__version__}",
        f"Python {sys.version.split()[0]} on {platform.system()} {platform.release()}",
        f"Patterns:  {', '.join(sorted(pattern_registry.names()))}",
        f"Providers: {', '.join(sorted(provider_registry.names()))}",
        f"Storage:   {', '.join(sorted(storage_registry.names()))}",
        "",
        "Quick start:",
        "  palm status              # live dashboard",
        "  palm doctor              # full health report",
        "  palm repl                # interactive shell",
        "  palm flow start onboard",
        "  palm start parallel-demo",
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
