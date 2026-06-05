"""
Centralized logging configuration for Palm.

Uses Python's logging + Rich for beautiful console output when running the CLI.
"""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler


def get_logger(name: str = "palm") -> logging.Logger:
    """Return a namespaced Palm logger."""
    return logging.getLogger(name)


def configure_logging(
    level: str = "INFO",
    *,
    console: Console | None = None,
    rich_tracebacks: bool = True,
) -> None:
    """
    Configure root + palm loggers with a nice RichHandler.

    Call this once early in CLI startup (or daemon entry points).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = RichHandler(
        console=console,
        rich_tracebacks=rich_tracebacks,
        show_time=True,
        show_path=False,
        markup=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Configure the palm logger specifically
    palm_logger = logging.getLogger("palm")
    palm_logger.setLevel(log_level)
    palm_logger.handlers.clear()
    palm_logger.addHandler(handler)
    palm_logger.propagate = False

    # Also make sure root doesn't double-log in simple cases
    logging.getLogger().setLevel(log_level)


# Convenience logger instance many modules can import
logger: logging.Logger = get_logger("palm")
