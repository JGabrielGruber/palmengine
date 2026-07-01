"""Tests for operator view format registry."""

from __future__ import annotations

import pytest

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.view_registry import (
    OperatorViewContext,
    allowed_view_formats,
    build_operator_view,
    clear_operator_view_builders,
    normalize_view_format,
    register_operator_view_builder,
)


def _wizard_flat() -> dict:
    return {
        "instance_id": "inst-1",
        "job_id": "job-1",
        "flow_name": "onboard",
        "status": "WAITING_FOR_INPUT",
        "current_step_slug": "intro",
        "prompt": {
            "step": "intro",
            "text": "Welcome",
            "field_type": "choice",
            "step_kind": "input",
            "choices": ["yes", "no"],
        },
        "answers": {},
    }


def _job_flat() -> dict:
    return {
        "job_id": "job-1",
        "status": "WAITING_FOR_INPUT",
        "pattern": {
            "pattern": "wizard",
            "step": "step_1",
            "field_type": "text",
            "prompt": "Name?",
            "answers": {"step_0": "ok"},
        },
        "instance": {"instance_id": "inst-1", "flow_name": "onboard"},
    }


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    clear_operator_view_builders()
    yield
    clear_operator_view_builders()


def test_normalize_compact_alias() -> None:
    assert normalize_view_format("compact") == "powertool"
    assert normalize_view_format("powertool") == "powertool"


def test_allowed_formats_include_powertool_and_verbose() -> None:
    assert allowed_view_formats() == frozenset({"powertool", "verbose"})


def test_powertool_wizard_matches_compact_wizard_inspect() -> None:
    flat = _wizard_flat()
    expected = compact_wizard_inspect(flat)
    payload = build_operator_view("powertool", flat_view=flat)
    assert payload == expected


def test_powertool_job_context_shape() -> None:
    payload = build_operator_view("powertool", flat_view=_job_flat())
    assert payload["job_id"] == "job-1"
    assert payload["instance_id"] == "inst-1"
    assert payload["step"] == "step_1"


def test_compact_alias_builds_powertool() -> None:
    payload = build_operator_view("compact", flat_view=_wizard_flat())
    assert payload["instance_id"] == "inst-1"
    assert payload["step"] == "intro"


def test_verbose_passthrough() -> None:
    flat = _wizard_flat()
    assert build_operator_view("verbose", flat_view=flat) == flat


def test_unknown_format_raises() -> None:
    with pytest.raises(ValueError, match="unknown operator view format"):
        build_operator_view("assistant", flat_view=_wizard_flat())


def test_register_custom_builder() -> None:
    def assistant_stub(
        flat_view: dict,
        *,
        context: OperatorViewContext,
    ) -> dict:
        return {"question": flat_view.get("prompt", {}).get("text"), "session_id": context.session_id}

    register_operator_view_builder("assistant", assistant_stub)
    ctx = OperatorViewContext(session_id="inst-9")
    payload = build_operator_view("assistant", flat_view=_wizard_flat(), context=ctx)
    assert payload["question"] == "Welcome"
    assert payload["session_id"] == "inst-9"
    assert "assistant" in allowed_view_formats()