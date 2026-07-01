"""Tests for per-service domain contracts (no transport entries)."""

from __future__ import annotations

import ast
import pathlib

from palm.services.definitions.registry import CatalogVerb, catalog_verbs
from palm.services.execution.flows.registry import CommandSpec, flow_commands
from palm.services.execution.providers.registry import InvokeVerb, invoke_verbs
from palm.services.system.registry import ObserveVerb, observe_verbs


def test_definitions_registry_has_catalog_verbs() -> None:
    verbs = catalog_verbs()
    assert verbs
    assert all(isinstance(verb, CatalogVerb) for verb in verbs)
    ids = {verb.verb_id for verb in verbs}
    assert "list_flows" in ids
    assert "validate_flow" in ids


def test_flow_registry_has_command_specs() -> None:
    commands = flow_commands()
    assert commands
    assert all(isinstance(spec, CommandSpec) for spec in commands)
    ids = {spec.command_id for spec in commands}
    assert "create_session" in ids
    assert "session_input" in ids
    assert all("method" not in spec.__dict__ for spec in commands)
    assert all("path" not in spec.__dict__ for spec in commands)


def test_system_registry_has_observe_verbs() -> None:
    verbs = observe_verbs()
    assert any(verb.verb_id == "doctor" for verb in observe_verbs())
    assert all(isinstance(verb, ObserveVerb) for verb in verbs)


def test_provider_registry_has_invoke_verbs() -> None:
    verbs = invoke_verbs()
    assert any(verb.operation == "invoke" for verb in verbs)
    assert all(isinstance(verb, InvokeVerb) for verb in verbs)


def test_service_registries_contain_no_http_literals() -> None:
    services_root = pathlib.Path("src/palm/services")
    offenders: list[str] = []
    for path in services_root.rglob("registry.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.startswith("/v1") or "HTTP" in node.value:
                    offenders.append(f"{path}:{node.lineno}")
    assert offenders == []