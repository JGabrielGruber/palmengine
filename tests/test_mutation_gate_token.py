"""Tests for CSRF-style input_token mutation gate (0.23.0)."""

from __future__ import annotations

import pytest

from palm.common.exceptions import MutationRejectedError
from palm.common.operator.mutation_gate import (
    TOKEN_TTL_SECONDS,
    assert_on_write,
    build_mutation_envelope,
    issue_input_token,
    require_input_token_enabled,
    require_mutation_token,
    should_validate_mutation,
    validate_input_token,
)


def test_issue_and_validate_round_trip() -> None:
    gate = issue_input_token(
        session_id="inst-1",
        step_slug="intent",
        secret="test-secret",
    )
    assert validate_input_token(
        token=gate["input_token"],
        session_id="inst-1",
        step_slug="intent",
        secret="test-secret",
    )


def test_reject_wrong_step() -> None:
    gate = issue_input_token(session_id="inst-1", step_slug="intent", secret="s")
    assert not validate_input_token(
        token=gate["input_token"],
        session_id="inst-1",
        step_slug="summary",
        secret="s",
    )


def test_reject_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    gate = issue_input_token(
        session_id="inst-1",
        step_slug="intent",
        secret="s",
        ttl_seconds=60,
    )
    nonce, issued_at, digest = gate["input_token"].split(".", 2)
    expired_at = str(int(issued_at) - TOKEN_TTL_SECONDS - 10)
    stale = f"{nonce}.{expired_at}.{digest}"
    assert not validate_input_token(
        token=stale,
        session_id="inst-1",
        step_slug="intent",
        secret="s",
    )


def test_build_mutation_envelope_omits_token_without_stored_gate() -> None:
    env = build_mutation_envelope(
        {
            "status": "WAITING_FOR_INPUT",
            "step": "intent",
            "field_type": "choice",
        },
    )
    assert env["mutations_allowed"] is True
    assert "input_token" not in env


def test_build_mutation_envelope_reuses_stored_gate() -> None:
    stored = issue_input_token(
        session_id="inst-1",
        step_slug="intent",
        secret="test-secret",
    )
    env = build_mutation_envelope(
        {"status": "WAITING_FOR_INPUT", "step": "intent"},
        stored_gate=stored,
    )
    assert env["input_token"] == stored["input_token"]


def test_should_validate_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PALM_MCP_REQUIRE_INPUT_TOKEN", raising=False)
    assert not should_validate_mutation({})
    assert should_validate_mutation({"input_token": "tok"})
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    assert should_validate_mutation({})


def test_assert_on_write_skipped_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PALM_MCP_REQUIRE_INPUT_TOKEN", raising=False)
    assert_on_write(
        {},
        session_id="inst-1",
        instance_metadata={},
        inspect={"status": "WAITING_FOR_INPUT", "step": "intent"},
    )


def test_assert_on_write_rejects_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    monkeypatch.setenv("PALM_MUTATION_SECRET", "test-secret")
    with pytest.raises(MutationRejectedError, match="mutation_rejected"):
        assert_on_write(
            {},
            session_id="inst-1",
            instance_metadata={},
            inspect={"status": "WAITING_FOR_INPUT", "step": "intent"},
        )


def test_assert_on_write_accepts_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    monkeypatch.setenv("PALM_MUTATION_SECRET", "test-secret")
    gate = issue_input_token(session_id="inst-1", step_slug="intent", secret="test-secret")
    assert_on_write(
        {"input_token": gate["input_token"]},
        session_id="inst-1",
        instance_metadata={"mutation_gate": gate},
        inspect={"status": "WAITING_FOR_INPUT", "step": "intent"},
    )


def test_require_mutation_token_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    monkeypatch.setenv("PALM_MUTATION_SECRET", "test-secret")
    with pytest.raises(MutationRejectedError, match="mutation_rejected"):
        require_mutation_token(
            {},
            session_id="inst-1",
            instance_metadata={},
            inspect={"status": "WAITING_FOR_INPUT", "step": "intent"},
        )


def test_require_input_token_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "1")
    assert require_input_token_enabled()
    monkeypatch.setenv("PALM_MCP_REQUIRE_INPUT_TOKEN", "0")
    assert not require_input_token_enabled()