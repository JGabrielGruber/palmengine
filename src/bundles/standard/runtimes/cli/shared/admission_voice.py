"""CLI honest voice for closed admission / missing organ (not bare RuntimeError)."""

from __future__ import annotations

from typing import Any


def format_cli_error(exc: BaseException) -> str:
    """Rich markup for operator errors — label gate refusals explicitly."""
    from palm.system.structure.errors import (
        AdmissionRefusedError,
        CapabilityRefusedError,
    )

    if isinstance(exc, AdmissionRefusedError):
        return f"[bold red]admission_refused[/] — {exc}"
    if isinstance(exc, CapabilityRefusedError):
        return f"[bold red]capability_refused[/] — {exc}"
    return f"[red]{exc}[/]"


def print_cli_error(console: Any, exc: BaseException) -> None:
    """Print a business start / continue error with honest admission branding."""
    console.print(format_cli_error(exc))


__all__ = [
    "format_cli_error",
    "print_cli_error",
]
