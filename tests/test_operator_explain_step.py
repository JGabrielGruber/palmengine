"""Tests for flow step explanation helper."""

from __future__ import annotations

from palm.common.operator.explain_step import explain_flow_step


def test_explain_flow_step_finds_slug() -> None:
    explained = explain_flow_step(
        {
            "name": "onboard",
            "pattern": "wizard",
            "options": {
                "steps": [
                    {
                        "slug": "name",
                        "title": "Name",
                        "prompt": "Your name?",
                        "field_type": "text",
                    }
                ]
            },
        },
        "name",
    )
    assert explained is not None
    assert explained["slug"] == "name"
    assert explained["field_type"] == "text"