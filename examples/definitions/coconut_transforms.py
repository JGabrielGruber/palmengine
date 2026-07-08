"""Coconut NPC transform rules — profile hydrate/sync for KV persistence."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.registration import register_transform
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode
from palm.patterns.wizard.bindings.context.keys import WizardKeys

MOOD_BY_REPUTATION: dict[str, str] = {
    "friend": "\"Good. Friends get the sweet coconuts and the good rumors.\"",
    "stranger": "\"Strangers pay full price and get the boring rumors.\"",
    "trouble": "\"Trouble gets watched. And the coconuts with the soft spots.\"",
}

RETURNING_TOPIC_BY_REPUTATION: dict[str, str] = {
    "friend": (
        "*(She grins — she knows your face.)*\n\n"
        "\"Welcome back, friend. Rumors, trade, or are you done for today?\""
    ),
    "stranger": (
        "*(She squints, not quite placing you.)*\n\n"
        "\"Still a stranger, then. Rumors, trade, or on your way?\""
    ),
    "trouble": (
        "*(She keeps one hand near the scales.)*\n\n"
        "\"Trouble again. Rumors, trade, or walk away while you can?\""
    ),
}

FIRST_TOPIC_PROMPT = (
    "*(She leans on the cart.)*\n\n"
    "\"Well then. What'll it be?\""
)


class CoconutHydrateProfileRule(BaseTransformRule):
    """Build ``player_profile`` from a ``load-coconut-player`` KV result."""

    name: ClassVar[str] = "coconut_hydrate_profile"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> CoconutHydrateProfileRule:
        return cls()

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        load_result = context.value if isinstance(context.value, dict) else {}
        profile = dict(load_result.get("value") or {})
        prior_visits = int(profile.get("visit_count") or 0)
        profile["visit_count"] = prior_visits + 1
        profile.setdefault("coconuts_owned", 0)
        profile["is_returning"] = profile["visit_count"] > 1
        if profile["is_returning"]:
            profile["returning_note"] = " I remember you."
        else:
            profile["returning_note"] = ""

        player_name = _answer(context, "player_name")
        if player_name:
            profile["player_name"] = player_name

        return context.advance(self.rule_name, profile, meta={"visit_count": profile["visit_count"]})


class CoconutPrepareReturningRule(BaseTransformRule):
    """Skip reputation for returning travelers; restore mood and topic copy."""

    name: ClassVar[str] = "coconut_prepare_returning"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> CoconutPrepareReturningRule:
        return cls()

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        profile = dict(context.value) if isinstance(context.value, dict) else {}
        if not profile.get("is_returning"):
            return context.advance(self.rule_name, profile)

        reputation = str(profile.get("reputation") or "stranger").strip().lower()
        if reputation not in MOOD_BY_REPUTATION:
            reputation = "stranger"

        _merge_answers(
            context,
            {
                "reputation": reputation,
                "mood_line": MOOD_BY_REPUTATION[reputation],
                "topic_prompt": RETURNING_TOPIC_BY_REPUTATION[reputation],
            },
        )
        if context.state is not None:
            context.state.set(WizardKeys.JUMP_TO_STEP, "topic")

        return context.advance(
            self.rule_name,
            profile,
            meta={"skipped_reputation": True, "reputation": reputation},
        )


class CoconutFirstTopicPromptRule(BaseTransformRule):
    """Default hub-menu copy for first-time visitors after reputation is chosen."""

    name: ClassVar[str] = "coconut_first_topic_prompt"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> CoconutFirstTopicPromptRule:
        return cls()

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        return context.advance(self.rule_name, FIRST_TOPIC_PROMPT)


class CoconutSyncProfileRule(BaseTransformRule):
    """Merge wizard answers into ``player_profile`` before KV save."""

    name: ClassVar[str] = "coconut_sync_profile"
    mode: ClassVar[TransformMode] = TransformMode.SINGLE

    @classmethod
    def from_options(cls, **options: Any) -> CoconutSyncProfileRule:
        return cls()

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        profile = dict(context.value) if isinstance(context.value, dict) else {}
        for key in ("reputation", "topic", "player_name"):
            value = _answer(context, key)
            if value is not None and value != "":
                if key == "topic":
                    profile["last_topic"] = value
                else:
                    profile[key] = value

        owned = int(profile.get("coconuts_owned") or 0)
        trade_choice = _answer(context, "trade")
        trade_buy_choice = _answer(context, "trade_buy")
        if trade_choice == "buy" or trade_buy_choice == "buy":
            profile["coconuts_owned"] = owned + 1
        else:
            profile["coconuts_owned"] = owned

        return context.advance(self.rule_name, profile)


def _merge_answers(context: TransformContext, updates: dict[str, Any]) -> None:
    state = context.state
    if state is None:
        return
    answers = dict(state.get(WizardKeys.ANSWERS) or {})
    answers.update(updates)
    state.set(WizardKeys.ANSWERS, answers)


def _answer(context: TransformContext, key: str) -> Any:
    state = context.state
    if state is None:
        return None
    answers = state.get(WizardKeys.ANSWERS)
    if isinstance(answers, dict) and key in answers:
        return answers[key]
    return state.get(key)


def register_coconut_transforms() -> None:
    register_transform("coconut_hydrate_profile", CoconutHydrateProfileRule)
    register_transform("coconut_prepare_returning", CoconutPrepareReturningRule)
    register_transform("coconut_first_topic_prompt", CoconutFirstTopicPromptRule)
    register_transform("coconut_sync_profile", CoconutSyncProfileRule)


__all__ = [
    "CoconutFirstTopicPromptRule",
    "CoconutHydrateProfileRule",
    "CoconutPrepareReturningRule",
    "CoconutSyncProfileRule",
    "FIRST_TOPIC_PROMPT",
    "MOOD_BY_REPUTATION",
    "RETURNING_TOPIC_BY_REPUTATION",
    "register_coconut_transforms",
]