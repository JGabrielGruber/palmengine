"""Tests for core resource wait policy resolution."""

from __future__ import annotations

from palm.core.resource.invocation import ResourceWaitOptions, WaitMode, parse_wait_mode


def test_parse_wait_mode_values() -> None:
    assert parse_wait_mode("until_input") == WaitMode.UNTIL_INPUT
    assert parse_wait_mode("until-terminal") == WaitMode.UNTIL_TERMINAL
    assert parse_wait_mode("fire_and_forget") == WaitMode.FIRE_AND_FORGET
    assert parse_wait_mode("invalid") is None


def test_resource_wait_options_from_params() -> None:
    opts = ResourceWaitOptions.from_params(
        {"wait": True, "timeout_seconds": 120},
    )
    assert opts.mode == WaitMode.UNTIL_TERMINAL
    assert opts.timeout_seconds == 120.0
    assert opts.should_wait is True

    until_input = ResourceWaitOptions.from_params({"wait_mode": "until_input"})
    assert until_input.mode == WaitMode.UNTIL_INPUT
    assert until_input.should_wait is True

    forget = ResourceWaitOptions.from_params({"wait": False})
    assert forget.mode == WaitMode.FIRE_AND_FORGET
    assert forget.should_wait is False