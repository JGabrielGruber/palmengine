"""Process catalog API shapes for the definitions service."""

from __future__ import annotations

from typing import Any

from palm.definitions.process import ProcessDefinition


def process_catalog_row(process: ProcessDefinition) -> dict[str, Any]:
    """Catalog list row — facts only."""
    return process.catalog_summary()


__all__ = ["process_catalog_row"]