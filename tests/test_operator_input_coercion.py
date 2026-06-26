"""Tests for operator input coercion helpers."""

from __future__ import annotations

from palm.common.operator.input_coercion import (
    coerce_job_input,
    resolve_mcp_job_input,
    resolve_mcp_wizard_input,
)


def test_coerce_confirm_yes_to_bool() -> None:
    assert coerce_job_input("yes", {"field_type": "confirm"}) is True
    assert coerce_job_input("no", {"field_type": "confirm"}) is False


def test_coerce_plain_text_unchanged() -> None:
    assert coerce_job_input("Ada Lovelace", {"field_type": "text"}) == "Ada Lovelace"


def test_resolve_mcp_wizard_input_prefers_plain_input() -> None:
    wizard = {
        "prompt": {"field_type": "text"},
        "answers": {},
    }
    assert resolve_mcp_wizard_input(input="Ada", value=None, wizard_view=wizard) == "Ada"


def test_resolve_mcp_wizard_input_confirm_string() -> None:
    wizard = {"prompt": {"field_type": "confirm"}, "answers": {}}
    assert resolve_mcp_wizard_input(input="yes", value=None, wizard_view=wizard) is True


def test_resolve_mcp_job_input_confirm_string() -> None:
    context = {"pattern": {"field_type": "confirm"}}
    assert resolve_mcp_job_input(input="yes", value=None, job_context=context) is True