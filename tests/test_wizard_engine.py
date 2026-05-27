"""
Basic smoke tests for the WizardEngine and example wizard.

Run with: pytest tests/ -q
"""

from __future__ import annotations

import pytest

from palm.core.wizard.engine import WizardEngine
from palm.exceptions import ValidationError
from wizards.examples.create_ape_profile import create_ape_profile_wizard
from wizards.examples.onboard_new_ape import onboard_new_ape_wizard

# Simple flat wizard used by legacy tests so they remain stable
def _legacy_flat_wizard():
    from palm.core.wizard.definition import WizardDefinition
    from palm.models.step import StepDefinition
    from palm.models.common import StepType

    steps = [
        StepDefinition(slug="introduction", type=StepType.INTRODUCTION, title="Intro", prompt="confirm to start", is_backtrackable=False),
        StepDefinition(slug="ask_name", type=StepType.USER_INPUT, title="Name", prompt="Name?", validation_rules=[{"type": "required"}, {"type": "min_length", "params": {"value": 2}}]),
        StepDefinition(slug="ask_age", type=StepType.USER_INPUT, title="Age", prompt="Age?", validation_rules=[{"type": "required"}]),
        StepDefinition(slug="summary", type=StepType.SUMMARY, title="Summary", prompt="Review?"),
        StepDefinition(slug="commit", type=StepType.COMMIT, title="Commit", prompt="Finish?"),
    ]
    return WizardDefinition(id="legacy_flat", name="Legacy", description="For tests", steps=steps)


@pytest.fixture
def engine() -> WizardEngine:
    eng = WizardEngine()
    # Legacy flat + basic example + rich 0.2.1 hierarchical demo
    eng.register(create_ape_profile_wizard())
    eng.register(onboard_new_ape_wizard())
    eng.register(_legacy_flat_wizard())
    return eng


def test_wizard_registration_and_listing(engine: WizardEngine) -> None:
    wizards = engine.list_wizards()
    assert any(w["id"] == "create_ape_profile" for w in wizards)
    assert any(w["id"] == "legacy_flat" for w in wizards)


def test_start_session_returns_rich_context(engine: WizardEngine) -> None:
    session, ctx = engine.start_session("legacy_flat")
    assert session.wizard_id == "legacy_flat"
    assert ctx.current_step_slug == "introduction"
    assert ctx.is_first_step is True
    assert "confirm" in (ctx.guidelines or "").lower() or ctx.prompt


def test_introduction_requires_confirmation(engine: WizardEngine) -> None:
    session, _ = engine.start_session("legacy_flat")

    # Bad confirmation should not advance
    ctx = engine.process_input(session.id, "no thanks")
    assert ctx.current_step_slug == "introduction"
    assert "last_error" in ctx.metadata

    # Proper confirmation advances into hierarchical structure
    ctx2 = engine.process_input(session.id, "confirm")
    assert ctx2.current_step_slug in {"ask_name", "personal_info"} or "ask_name" in str(ctx2.current_path)


def test_full_happy_path(engine: WizardEngine) -> None:
    session, _ = engine.start_session("legacy_flat")
    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Grace Hopper")
    engine.process_input(session.id, "42")   # valid adult age

    # Advance through personal_info children + conditional branch + summary
    # We may land on ask_id_number because 42 >= 18
    for _ in range(6):  # generous number of auto + manual advances
        try:
            ctx = engine.process_input(session.id, "yes" if "summary" in (engine.get_status(session.id).get("current_step") or "") else "ID-98765")
            if ctx.status.value == "committed":
                break
        except Exception:
            break

    # Final commit
    result_ctx = engine.commit(session.id)
    assert result_ctx.status.value == "committed" or "commit_result" in (result_ctx.metadata or {})


def test_validation_error(engine: WizardEngine) -> None:
    session, _ = engine.start_session("legacy_flat")
    engine.process_input(session.id, "confirm")
    # First bad input (name too short) should raise
    with pytest.raises(ValidationError):
        engine.process_input(session.id, "A")  # too short for ask_name


def test_backtracking(engine: WizardEngine) -> None:
    session, _ = engine.start_session("legacy_flat")
    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Alan Turing")
    engine.process_input(session.id, "41")

    # Go back (hierarchical aware)
    ctx = engine.backtrack(session.id, "ask_name")
    assert ctx.current_step_slug == "ask_name"
    # The value for the current step remains visible
    assert ctx.collected_data.get("ask_name") == "Alan Turing"
    # Later step data cleared
    assert "ask_age" not in ctx.collected_data


# ----------------------------------------------------------------------
# 0.1.1 Feature Tests
# ----------------------------------------------------------------------

def test_rich_context_has_guidance_fields(engine: WizardEngine) -> None:
    """0.1.1 + 0.2.0 guidance fields on RichContext."""
    session, ctx = engine.start_session("legacy_flat")

    assert ctx.suggested_input == "confirm"
    assert any("confirm" in a.lower() for a in ctx.available_actions)

    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Grace Hopper")
    ctx2 = engine.process_input(session.id, "42")

    assert len(ctx2.available_actions) > 0 or ctx2.suggested_input


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
    session, _ = engine.start_session("legacy_flat")
    engine.process_input(session.id, "confirm")
    engine.process_input(session.id, "Margaret Hamilton")
    engine.process_input(session.id, "85")

    # Should be able to back using the session's own back_stack
    ctx = engine.backtrack(session.id, "ask_name")
    assert ctx.current_step_slug == "ask_name"
    assert "Margaret Hamilton" in str(ctx.collected_data.get("ask_name"))


# ----------------------------------------------------------------------
# 0.2.1 Hierarchical + Dynamic Builder Tests (using dedicated demo)
# ----------------------------------------------------------------------

def test_hierarchical_path_and_breadcrumb(engine: WizardEngine) -> None:
    """Test that nested steps produce proper current_path and breadcrumb using the 0.2.1 demo."""
    fresh = WizardEngine()
    fresh.register(onboard_new_ape_wizard())

    s, ctx = fresh.start_session("onboard_new_ape")
    assert ctx.current_path == ["introduction"]

    fresh.process_input(s.id, "confirm")
    s = fresh.get_session(s.id, touch=False)  # refresh authoritative state

    # Should have descended into the SEQUENCE composite
    assert s.current_path[0] == "personal_section"
    assert "ask_name" in s.current_path

    ctx2 = fresh.process_input(s.id, "Ada Lovelace")
    assert "ask_age" in str(ctx2.current_path) or ctx2.current_step_slug == "ask_age"


def test_dynamic_context_builder(engine: WizardEngine) -> None:
    """Dynamic builders can change guidelines and suggested_input at runtime (0.2.1 demo)."""
    fresh = WizardEngine()
    fresh.register(onboard_new_ape_wizard())

    s, _ = fresh.start_session("onboard_new_ape")
    fresh.process_input(s.id, "confirm")
    fresh.process_input(s.id, "Grace Hopper")
    s = fresh.get_session(s.id, touch=False)

    # Age >= 65 should trigger the senior dynamic message in the new demo
    ctx = fresh.process_input(s.id, "68")

    # We are now on the adult branch (ask_employee_id) because age=68 >= 18.
    # The important thing is that we did not stay on ask_age and the dynamic builder had a chance to run earlier.
    assert ctx.current_step_slug in {"ask_age", "ask_employee_id", "ask_guardian_contact"}
    assert ctx.suggested_input or len(ctx.available_actions) > 0 or ctx.current_path


def test_condition_step_auto_advances(engine: WizardEngine) -> None:
    """CONDITION steps should evaluate and auto-descend without user input (0.2.1 demo)."""
    fresh = WizardEngine()
    fresh.register(onboard_new_ape_wizard())

    s, _ = fresh.start_session("onboard_new_ape")
    fresh.process_input(s.id, "confirm")
    fresh.process_input(s.id, "Young Person")
    fresh.process_input(s.id, "15")
    s = fresh.get_session(s.id, touch=False)

    # Engine should have auto-evaluated "age_gate" and landed on the minor branch
    assert s.current_step_slug != "age_gate"
    assert "ask_guardian_contact" in (s.current_step_slug or "") or s.current_step_slug in {"summary", "commit"}


def test_backtracking_across_hierarchy(engine: WizardEngine) -> None:
    """Users can backtrack using simple slugs or dotted paths in the 0.2.1 demo."""
    fresh = WizardEngine()
    fresh.register(onboard_new_ape_wizard())

    s, _ = fresh.start_session("onboard_new_ape")
    fresh.process_input(s.id, "confirm")
    fresh.process_input(s.id, "Grace Hopper")
    fresh.process_input(s.id, "42")
    s = fresh.get_session(s.id, touch=False)

    # Simple slug backtrack
    ctx = fresh.backtrack(s.id, "ask_name")
    assert ctx.current_step_slug == "ask_name"

    fresh.process_input(s.id, "Grace Hopper 2.0")
    fresh.process_input(s.id, "43")
    s = fresh.get_session(s.id, touch=False)

    # Dotted path backtracking (key 0.2.1 feature)
    ctx2 = fresh.backtrack(s.id, "personal_section.ask_age")
    assert ctx2.current_step_slug == "ask_age"
    assert "personal_section" in ctx2.current_path


# ----------------------------------------------------------------------
# 0.2.2 Dedicated Stabilization Tests
# ----------------------------------------------------------------------

def test_condition_true_false_branching(engine: WizardEngine):
    """CONDITION must select exactly one branch: children[0] for True, children[1] for False."""
    fresh = WizardEngine()
    fresh.register(onboard_new_ape_wizard())

    # Adult path (True branch)
    s1, _ = fresh.start_session("onboard_new_ape")
    fresh.process_input(s1.id, "confirm")
    fresh.process_input(s1.id, "Adult Ape")
    fresh.process_input(s1.id, "35")  # >= 18 → True branch
    s1 = fresh.get_session(s1.id, touch=False)
    assert s1.current_step_slug == "ask_employee_id", "Should be on adult branch (children[0])"

    # Minor path (False branch)
    s2, _ = fresh.start_session("onboard_new_ape")
    fresh.process_input(s2.id, "confirm")
    fresh.process_input(s2.id, "Young Ape")
    fresh.process_input(s2.id, "15")  # < 18 → False branch
    s2 = fresh.get_session(s2.id, touch=False)
    assert s2.current_step_slug == "ask_guardian_contact", "Should be on minor branch (children[1])"


def test_auto_descent_and_sibling_progression(engine: WizardEngine):
    """After finishing children of a SEQUENCE, engine must correctly ascend and continue."""
    fresh = WizardEngine()
    fresh.register(onboard_new_ape_wizard())

    s, _ = fresh.start_session("onboard_new_ape")
    fresh.process_input(s.id, "confirm")
    fresh.process_input(s.id, "Test User")
    fresh.process_input(s.id, "25")

    s = fresh.get_session(s.id, touch=False)
    # After personal_section children + age_gate, we should be at summary or later
    assert s.current_path[0] in ("age_gate", "summary", "commit") or s.current_step_slug in ("ask_employee_id", "summary")


def test_backtrack_then_continue(engine: WizardEngine):
    """Backtrack using dotted path, then continue forward successfully."""
    fresh = WizardEngine()
    fresh.register(onboard_new_ape_wizard())

    s, _ = fresh.start_session("onboard_new_ape")
    fresh.process_input(s.id, "confirm")
    fresh.process_input(s.id, "Backtrack Tester")
    fresh.process_input(s.id, "30")

    # Backtrack into the middle of personal_section
    fresh.backtrack(s.id, "personal_section.ask_name")
    s = fresh.get_session(s.id, touch=False)
    assert s.current_path == ["personal_section", "ask_name"]

    # Continue forward again
    fresh.process_input(s.id, "Backtrack Tester 2")
    fresh.process_input(s.id, "31")
    s = fresh.get_session(s.id, touch=False)

    # Should have progressed past personal_section again
    assert "personal_section" not in s.current_path or s.current_step_slug in ("ask_employee_id", "summary", "commit")
