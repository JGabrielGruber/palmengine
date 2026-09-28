"""Parse definition payloads for catalog CRUD writes."""

from __future__ import annotations

from typing import Any

from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.definitions.resource import ResourceDefinition


def parse_flow(body: dict[str, Any]) -> FlowDefinition:
    return FlowDefinition.from_dict(body)


def parse_process(body: dict[str, Any]) -> ProcessDefinition:
    return ProcessDefinition.from_dict(body)


def parse_resource(body: dict[str, Any]) -> ResourceDefinition:
    return ResourceDefinition.from_dict(body)


__all__ = ["parse_flow", "parse_process", "parse_resource"]