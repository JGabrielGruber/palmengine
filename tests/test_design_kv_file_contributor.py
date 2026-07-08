"""KV and file design contributors (0.28.3)."""

from __future__ import annotations

import pytest

import palm.providers  # noqa: F401 — register providers + design contributors
from palm.app import ApplicationHost, HostProfile, PalmSettings
from palm.providers.file.bindings.design import validate_file_design_proposal
from palm.providers.kv.bindings.design import validate_kv_design_proposal
from palm.services.design.registry import clear_design_contributors, iter_design_contributors


@pytest.fixture(autouse=True)
def _ensure_contributors_registered() -> None:
    clear_design_contributors()
    from palm.providers.file.bindings.design import register_file_design_contributor
    from palm.providers.kv.bindings.design import register_kv_design_contributor

    register_kv_design_contributor()
    register_file_design_contributor()
    yield
    clear_design_contributors()


@pytest.fixture
def design_host():
    settings = PalmSettings()
    with ApplicationHost(settings=settings, profile=HostProfile.all_in_one()) as host:
        yield host


def test_kv_and_file_contributors_register() -> None:
    contributor_ids = {row.contributor_id for row in iter_design_contributors()}
    assert contributor_ids == {"file", "kv"}


def test_validate_kv_design_proposal_accepts_coconut_load() -> None:
    body = {
        "name": "load-coconut-player",
        "provider": "kv",
        "action": "get",
        "resource_id": "players/{{ state.player_name }}",
        "params": {
            "namespace": "coconut",
            "backend": "auto",
            "default": {},
        },
    }
    valid, blockers = validate_kv_design_proposal(body, None)
    assert blockers == []
    assert valid is True


def test_validate_kv_design_proposal_rejects_invalid_action() -> None:
    body = {
        "name": "bad-kv",
        "provider": "kv",
        "action": "fetch",
        "resource_id": "players/alice",
        "params": {"namespace": "coconut"},
    }
    valid, blockers = validate_kv_design_proposal(body, None)
    assert valid is False
    assert any("action must be one of" in row for row in blockers)


def test_validate_file_design_proposal_accepts_json_write() -> None:
    body = {
        "name": "write-profile",
        "provider": "file",
        "action": "write",
        "resource_id": "profiles/alice.json",
        "params": {"format": "json", "content": {"visit_count": 1}},
    }
    valid, blockers = validate_file_design_proposal(body, None)
    assert blockers == []
    assert valid is True


def test_validate_file_design_proposal_rejects_traversal() -> None:
    body = {
        "name": "escape",
        "provider": "file",
        "action": "read",
        "resource_id": "../secret.json",
        "params": {"format": "json"},
    }
    valid, blockers = validate_file_design_proposal(body, None)
    assert valid is False
    assert any("relative document path" in row for row in blockers)


def test_propose_resource_accepts_kv_via_design_host(design_host) -> None:
    body = {
        "name": "design-kv-demo",
        "provider": "kv",
        "action": "get",
        "resource_id": "demo/{{ state.key }}",
        "params": {
            "namespace": "demo",
            "backend": "auto",
            "default": None,
        },
    }
    proposed = design_host.design.propose_resource(body)
    assert proposed["validation"]["valid"] is True


def test_propose_resource_rejects_invalid_kv_via_design_host(design_host) -> None:
    body = {
        "name": "design-kv-bad",
        "provider": "kv",
        "action": "put",
        "resource_id": "demo/key",
        "params": {"namespace": "bad namespace", "backend": "auto"},
    }
    proposed = design_host.design.propose_resource(body)
    assert proposed["validation"]["valid"] is False
    blockers = proposed["validation"].get("blockers") or []
    assert any("namespace" in row for row in blockers)