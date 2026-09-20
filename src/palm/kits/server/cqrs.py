"""Standalone CQRS wiring — re-export from common (server kit door)."""

from __future__ import annotations

from palm.common.cqrs.standalone import (
    StandaloneCommandHandlers,
    StandaloneQueryHandlers,
    wire_standalone_buses,
    wire_standalone_query_bus,
)

__all__ = [
    "StandaloneCommandHandlers",
    "StandaloneQueryHandlers",
    "wire_standalone_buses",
    "wire_standalone_query_bus",
]
