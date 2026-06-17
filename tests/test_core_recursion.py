"""Tests for general-purpose core recursion guard."""

from __future__ import annotations

import pytest

from palm.core.utils.recursion import (
    RecursionGuardError,
    RecursionLimits,
    chain_key,
    current_chain,
    current_depth,
    recursion_frame,
)


def test_chain_key_joins_parts() -> None:
    assert chain_key("flow", "ingest-etl") == "flow:ingest-etl"


def test_recursion_frame_tracks_depth_and_chain() -> None:
    assert current_depth() == 0
    assert current_chain() == ()
    with recursion_frame("flow:a") as (depth, chain):
        assert depth == 1
        assert chain == ("flow:a",)
        with recursion_frame("flow:b") as (depth2, chain2):
            assert depth2 == 2
            assert chain2 == ("flow:a", "flow:b")
    assert current_depth() == 0


def test_recursion_frame_detects_cycles() -> None:
    with pytest.raises(RecursionGuardError, match="Cycle detected"):
        with recursion_frame("flow:a"):
            with recursion_frame("flow:b"):
                with recursion_frame("flow:a"):
                    pass


def test_recursion_frame_enforces_depth_limit() -> None:
    limits = RecursionLimits(max_depth=1)
    with recursion_frame("flow:parent", limits=limits):
        with pytest.raises(RecursionGuardError, match="depth"):
            with recursion_frame("flow:child", limits=limits):
                pass