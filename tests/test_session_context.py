"""Tests for SessionContext read model."""

from __future__ import annotations

from palm.common.patterns._registry import clear_session_enrichers, register_session_enricher
from palm.core.orchestration import JobStatus
from palm.services.execution.flows.schemas import SessionContext, build_session_context


def test_build_session_context_core_fields() -> None:
    ctx = build_session_context(
        flow_id="approve",
        session_id="inst-1",
        view={
            "instance_id": "inst-1",
            "job_id": "job-1",
            "status": JobStatus.WAITING_FOR_INPUT.value,
            "metadata": {"pattern": "wizard", "flow": "approve"},
        },
    )
    assert ctx.session_id == "inst-1"
    assert ctx.flow_id == "approve"
    assert ctx.pattern == "wizard"
    assert ctx.waiting_for_input is True
    assert ["flows", "approve", "session", "inst-1", "input"] in ctx.next_commands


def test_session_context_to_dict() -> None:
    ctx = SessionContext(session_id="inst-1", flow_id="approve", status="RUNNING")
    payload = ctx.to_dict()
    assert payload["session_id"] == "inst-1"
    assert payload["flow_id"] == "approve"
    assert "next_commands" in payload


def test_pattern_session_enricher_hook() -> None:
    clear_session_enrichers()
    register_session_enricher("wizard", lambda view: {"prompt": view.get("prompt")})

    ctx = build_session_context(
        flow_id="onboard",
        session_id="inst-2",
        view={
            "status": JobStatus.RUNNING.value,
            "metadata": {"pattern": "wizard"},
            "prompt": "Name?",
        },
        enricher=lambda pattern, view: {"prompt": view.get("prompt")} if pattern == "wizard" else {},
    )
    assert ctx.detail.get("prompt") == "Name?"
    clear_session_enrichers()