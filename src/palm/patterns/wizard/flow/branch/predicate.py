"""Declarative branch predicates — same vocabulary as the ``conditional`` transform."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.core.context import BaseState
from palm.core.exceptions import TransformApplicationError
from palm.patterns.wizard.bindings.context.keys import WizardKeys
from palm.patterns.wizard.bindings.context.state import get_answers

_PREDICATE_KEYS = frozenset(
    {
        "equals",
        "not_equals",
        "gt",
        "gte",
        "lt",
        "lte",
        "is_truthy",
        "exists",
    },
)


def validate_when_clause(when: Mapping[str, Any]) -> None:
    """Raise when ``when`` omits a recognized predicate."""
    if not when:
        raise ValueError("branch step requires a non-empty when clause")
    if not any(key in when for key in _PREDICATE_KEYS):
        raise ValueError(
            "branch when requires a predicate (equals, gt, gte, is_truthy, exists, ...)",
        )


def evaluate_branch_predicate(state: BaseState, when: Mapping[str, Any]) -> bool:
    """Return whether the branch ``then`` arm should run."""
    validate_when_clause(when)
    field = when.get("field")
    answers = get_answers(state)
    subject: Any
    container: dict[str, Any] | None
    if field is not None:
        container = dict(answers) if isinstance(answers, dict) else {}
        subject = container.get(field)
        if subject is None:
            subject = state.get(field)
            if subject is None:
                subject = state.get(f"{WizardKeys.PREFIX}.{field}")
    else:
        container = dict(answers) if isinstance(answers, dict) else None
        subject = container if container is not None else state
    return _matches(subject, container, dict(when))


def _matches(subject: Any, container: dict[str, Any] | None, options: dict[str, Any]) -> bool:
    if "equals" in options:
        return bool(subject == options["equals"])
    if "not_equals" in options:
        return bool(subject != options["not_equals"])
    if "gt" in options:
        return bool(subject > options["gt"])
    if "gte" in options:
        return bool(subject >= options["gte"])
    if "lt" in options:
        return bool(subject < options["lt"])
    if "lte" in options:
        return bool(subject <= options["lte"])
    if options.get("is_truthy"):
        return bool(subject)
    if options.get("exists"):
        if container is None:
            return subject is not None
        field = options.get("field")
        return isinstance(container, dict) and field in container
    raise TransformApplicationError(
        "branch when requires a predicate (equals, gt, gte, is_truthy, exists, ...)",
    )


__all__ = ["evaluate_branch_predicate", "validate_when_clause"]