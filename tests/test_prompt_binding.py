"""Tests for wizard prompt ``{{ state.* }}`` interpolation (0.27.1)."""

from __future__ import annotations

from palm.common.operator.prompt_binding import resolve_wizard_prompt


def test_resolve_wizard_prompt_substitutes_state_key() -> None:
    text = '{{ state.mood_line }}\n\n"Well then. What\'ll it be?"'
    binding = {"mood_line": "Friends get sweet coconuts."}
    assert "Friends get sweet coconuts." in resolve_wizard_prompt(text, binding)
    assert "{{ state.mood_line }}" not in resolve_wizard_prompt(text, binding)


def test_resolve_wizard_prompt_missing_key_becomes_empty() -> None:
    text = "Hello {{ state.missing }}"
    assert resolve_wizard_prompt(text, {"other": "x"}) == "Hello "


def test_resolve_wizard_prompt_without_binding_returns_original() -> None:
    text = "Static prompt"
    assert resolve_wizard_prompt(text, None) == text
    assert resolve_wizard_prompt(text, {}) == text


def test_resolve_wizard_prompt_none_text() -> None:
    assert resolve_wizard_prompt(None, {"a": 1}) is None