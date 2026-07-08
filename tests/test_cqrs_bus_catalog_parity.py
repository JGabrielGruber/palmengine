"""CQRS type catalog parity — service-required types must exist in standalone mode."""

from __future__ import annotations

import palm.services.definitions.bindings.cqrs.contributor  # noqa: F401
import palm.services.design.bindings.cqrs.contributor  # noqa: F401

from palm.common.cqrs.catalog import collect_cqrs_command_types, collect_cqrs_query_types
from palm.services.definitions.bindings.cqrs.registry import (
    DEFINITIONS_COMMAND_TYPES,
    DEFINITIONS_QUERY_TYPES,
)
from palm.services.design.bindings.cqrs.registry import DESIGN_COMMAND_TYPES, DESIGN_QUERY_TYPES

SERVICE_COMMAND_TYPES = DEFINITIONS_COMMAND_TYPES + DESIGN_COMMAND_TYPES
SERVICE_QUERY_TYPES = DEFINITIONS_QUERY_TYPES + DESIGN_QUERY_TYPES


def test_standalone_catalog_includes_service_command_types() -> None:
    standalone = set(collect_cqrs_command_types(mode="standalone"))
    for command_type in SERVICE_COMMAND_TYPES:
        assert command_type in standalone, f"{command_type.__name__} missing from standalone"


def test_standalone_catalog_includes_service_query_types() -> None:
    standalone = set(collect_cqrs_query_types(mode="standalone"))
    for query_type in SERVICE_QUERY_TYPES:
        assert query_type in standalone, f"{query_type.__name__} missing from standalone"


def test_host_catalog_is_superset_of_standalone_commands() -> None:
    host = set(collect_cqrs_command_types(mode="host"))
    standalone = set(collect_cqrs_command_types(mode="standalone"))
    assert standalone <= host


def test_host_catalog_is_superset_of_standalone_queries() -> None:
    host = set(collect_cqrs_query_types(mode="host"))
    standalone = set(collect_cqrs_query_types(mode="standalone"))
    assert standalone <= host