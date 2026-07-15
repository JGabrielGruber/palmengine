"""Append a single item to a list in blackboard state (ring-buffer friendly)."""

from __future__ import annotations

from typing import Any, ClassVar

from palm.core.exceptions import TransformApplicationError
from palm.core.transform.base import BaseTransformRule, TransformContext


class AppendItemRule(BaseTransformRule):
    """
    Append ``context.value`` into a list at ``list_key`` / ``_target_key``.

    Options: ``max_items``, ``unique_field`` (dedup before append), ``prepend`` (default true).
    """

    name: ClassVar[str] = "append_item"

    @classmethod
    def from_options(cls, **options: Any) -> AppendItemRule:
        alias = options.get("alias")
        instance = cls()
        if alias is not None:
            instance._alias = str(alias)
        return instance

    def apply(self, context: TransformContext, **options: Any) -> TransformContext:
        if context.state is None:
            raise TransformApplicationError(f"{self.rule_name} requires blackboard state")

        item = context.value
        list_key = options.get("list_key") or options.get("_target_key")
        if not list_key:
            raise TransformApplicationError(
                f"{self.rule_name} requires list_key= or pipeline target_key",
            )

        existing = context.state.get(str(list_key))
        if existing is None:
            items: list[Any] = []
        elif isinstance(existing, list):
            items = list(existing)
        else:
            raise TransformApplicationError(
                f"{self.rule_name} expects a list at {list_key!r}, "
                f"got {type(existing).__name__}",
            )

        unique_field = options.get("unique_field")
        if unique_field and isinstance(item, dict):
            marker = item.get(str(unique_field))
            items = [
                entry
                for entry in items
                if not (isinstance(entry, dict) and entry.get(str(unique_field)) == marker)
            ]

        prepend = bool(options.get("prepend", True))
        if prepend:
            items.insert(0, item)
        else:
            items.append(item)

        max_items = options.get("max_items")
        if max_items is not None:
            cap = max(0, int(max_items))
            if cap == 0:
                items = []
            elif len(items) > cap:
                items = items[:cap] if prepend else items[-cap:]

        return context.advance(
            self.rule_name,
            items,
            meta={
                "list_key": str(list_key),
                "count": len(items),
                "prepend": prepend,
                "max_items": max_items,
                "unique_field": unique_field,
            },
        )


__all__ = ["AppendItemRule"]