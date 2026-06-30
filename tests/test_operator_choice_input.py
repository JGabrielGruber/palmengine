"""Tests for operator menu choice resolution."""

from __future__ import annotations

from palm.common.operator.choice_input import resolve_menu_choice


def test_resolve_menu_choice_exact_label() -> None:
    choices = ["Add a new item", "Continue to summary (2 items)"]
    assert resolve_menu_choice("Continue to summary (2 items)", choices) == choices[1]


def test_resolve_menu_choice_prefix() -> None:
    choices = ["Add a new item", "Continue to summary (2 items)"]
    assert resolve_menu_choice("Continue to summary", choices) == choices[1]


def test_resolve_menu_choice_number() -> None:
    choices = ["Add a new item", "Edit an item", "Continue to summary"]
    assert resolve_menu_choice("3", choices) == "Continue to summary"
