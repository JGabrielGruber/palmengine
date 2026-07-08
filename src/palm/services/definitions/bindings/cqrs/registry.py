"""Definitions service CQRS type catalog."""

from __future__ import annotations

from palm.common.cqrs.command import MigrateInstanceCommand
from palm.common.cqrs.query import AnalyzeDefinitionImpactQuery

DEFINITIONS_COMMAND_TYPES: tuple[type, ...] = (MigrateInstanceCommand,)
DEFINITIONS_QUERY_TYPES: tuple[type, ...] = (AnalyzeDefinitionImpactQuery,)

__all__ = ["DEFINITIONS_COMMAND_TYPES", "DEFINITIONS_QUERY_TYPES"]