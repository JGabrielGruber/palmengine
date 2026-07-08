"""Coconut NPC transform rules — profile hydrate/sync for KV persistence."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.common.transforms.registration import register_transform
from palm.core.transform.base import BaseTransformRule, TransformContext, TransformMode
from palm.patterns.wizard.bindings.context.keys import WizardKeys


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
    register_transform("coconut_sync_profile", CoconutSyncProfileRule)


__all__ = [
    "CoconutHydrateProfileRule",
    "CoconutSyncProfileRule",
    "register_coconut_transforms",
]