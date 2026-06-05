"""
Basic smoke tests for the WizardEngine and example wizard.

Run with: pytest tests/ -q
"""

from __future__ import annotations

import pytest

from palm.cli.solid.legacy.exceptions import ValidationError
from palm.cli.solid.legacy.wizard.engine import WizardEngine
from wizards.examples.create_ape_profile import create_ape_profile_wizard


@pytest.fixture
def engine() -> WizardEngine:
    eng = WizardEngine()
    eng.register(create_ape_profile_wizard())
    return eng


def test_wizard_registration_and_listing(engine: WizardEngine) -> None:
    wizards = engine.list_wizards()
    assert any(w["id"] == "create_ape_profile" for w in wizards)


def test_start_session_returns_rich_context(engine: WizardEngine) -> None:
    session, ctx = engine.start_session("create_ape_profile")
    assert session.wizard_id == "create_ape_profile"
    assert ctx.current_step_slug == "introduction"
    assert ctx.is_first_step is True
    assert "confirm" in (ctx.guidelines or "").lower() or ctx.prompt


def test_introduction_requires_confirmation(engine: WizardEngine) -> None:
    session, _ = engine.start_session("create_ape_profile")

    # Bad confirmation should not advance
    ctx = engine.process_input(session.id, "no thanks")
    assert ctx.current_step_slug == "introduction"
    assert "last_error" in ctx.metadata

    # Proper confirmation advances
    ctx2 = engine.process_input(session.id, "confirm")
    assert ctx2.current_step_slug == "ask_name"


def test_full_happy_path(engine: WizardEngine) -> None:
    session, _ = engine.start_session("create_ape_profile")
    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Grace Hopper")
    engine.process_input(session.id, "85")

    # summary step
    ctx = engine.process_input(session.id, "ok")
    assert ctx.current_step_slug == "summary" or ctx.current_step_slug == "commit"

    # Reach commit
    if ctx.current_step_slug == "summary":
        ctx = engine.process_input(session.id, "yes")

    # Final commit
    result_ctx = engine.commit(session.id)
    assert result_ctx.status.value == "committed" or "commit_result" in (result_ctx.metadata or {})


def test_validation_error(engine: WizardEngine) -> None:
    session, _ = engine.start_session("create_ape_profile")
    engine.process_input(session.id, "confirm")
    # First bad input (name too short) should raise
    with pytest.raises(ValidationError):
        engine.process_input(session.id, "A")


def test_backtracking(engine: WizardEngine) -> None:
    session, _ = engine.start_session("create_ape_profile")
    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Alan Turing")
    engine.process_input(session.id, "41")

    # Go back
    ctx = engine.backtrack(session.id, "ask_name")
    assert ctx.current_step_slug == "ask_name"
    # The value for the current step remains visible (user may want to keep or edit it)
    assert ctx.collected_data.get("ask_name") == "Alan Turing"
    # But later steps' data must have been cleared
    assert "ask_age" not in ctx.collected_data


# ----------------------------------------------------------------------
# 0.1.1 Feature Tests
# ----------------------------------------------------------------------


def test_rich_context_has_guidance_fields(engine: WizardEngine) -> None:
    """New 0.1.1 fields on RichContext for better UX guidance."""
    session, ctx = engine.start_session("create_ape_profile")

    # Introduction step should suggest confirmation
    assert ctx.suggested_input == "confirm"
    assert any("confirm" in a.lower() for a in ctx.available_actions)

    # Advance to a later step
    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Grace Hopper")
    ctx2 = engine.process_input(session.id, "42")

    # Summary or commit steps should also have strong guidance
    if ctx2.current_step_type in ("summary", "commit"):
        assert ctx2.suggested_input == "confirm"
        assert len(ctx2.available_actions) > 0


def test_commit_handler_registration(engine: WizardEngine) -> None:
    """Commit handlers can be registered together with the wizard (0.1.1)."""
    from wizards.examples.create_ape_profile import ape_profile_commit_handler

    fresh = WizardEngine()
    wiz = create_ape_profile_wizard()

    fresh.register(wiz, commit_handlers={"create_ape_profile_commit": ape_profile_commit_handler})

    assert "create_ape_profile_commit" in fresh._commit_handlers  # type: ignore[attr-defined]


def test_active_session_and_back_defaults(engine: WizardEngine) -> None:
    """
    The engine itself doesn't have 'active session' concept — that lives in the REPL.
    We test that backtracking still works cleanly after the 0.1.1 logic changes.
    """
    session, _ = engine.start_session("create_ape_profile")
    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Margaret Hamilton")
    engine.process_input(session.id, "85")

    # Should be able to back using the session's own back_stack
    ctx = engine.backtrack(session.id, "ask_name")
    assert ctx.current_step_slug == "ask_name"
    assert "Margaret Hamilton" in str(ctx.collected_data.get("ask_name"))
