"""
Validation engine for wizard step input.

Supports declarative rules + pluggable custom validators.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from palm.cli.solid.legacy.models.common import ValidationRule
from palm.cli.solid.legacy.models.step import StepDefinition

# Registry of custom validator functions
_custom_validators: dict[str, Callable[[Any, dict[str, Any]], str | None]] = {}


def register_validator(name: str, fn: Callable[[Any, dict[str, Any]], str | None]) -> None:
    """Register a custom validator. fn(value, params) -> error_message or None."""
    _custom_validators[name] = fn


def get_validator(name: str) -> Callable[[Any, dict[str, Any]], str | None] | None:
    return _custom_validators.get(name)


def validate_input(
    value: Any,
    step: StepDefinition,
    collected_data: dict[str, Any] | None = None,
) -> list[str]:
    """
    Validate a value against a step's rules.

    Returns list of error messages (empty = valid).
    """
    errors: list[str] = []
    collected_data = collected_data or {}

    for rule in step.validation_rules:
        err = _apply_rule(value, rule, step, collected_data)
        if err:
            errors.append(err)

    # Built-in required check
    if step.required and (value is None or (isinstance(value, str) and value.strip() == "")):
        errors.append("This field is required.")

    return errors


def _apply_rule(
    value: Any,
    rule: ValidationRule,
    step: StepDefinition,
    collected: dict[str, Any],
) -> str | None:
    """Apply a single rule. Returns error string or None."""
    rtype = rule.type.lower()
    params = rule.params

    if rtype == "required":
        if value is None or (isinstance(value, str) and not value.strip()):
            return rule.to_error(step.slug)

    elif rtype == "min_length":
        min_len = params.get("value", 1)
        if isinstance(value, str) and len(value) < min_len:
            return rule.to_error() or f"Must be at least {min_len} characters."

    elif rtype == "max_length":
        max_len = params.get("value", 256)
        if isinstance(value, str) and len(value) > max_len:
            return rule.to_error() or f"Must be at most {max_len} characters."

    elif rtype == "min_value":
        min_val = params.get("value")
        try:
            if value is not None and float(value) < float(min_val):
                return rule.to_error() or f"Must be at least {min_val}."
        except (TypeError, ValueError):
            return "Must be a number."

    elif rtype == "max_value":
        max_val = params.get("value")
        try:
            if value is not None and float(value) > float(max_val):
                return rule.to_error() or f"Must be at most {max_val}."
        except (TypeError, ValueError):
            return "Must be a number."

    elif rtype == "regex":
        pattern = params.get("pattern")
        if pattern and isinstance(value, str) and not re.match(pattern, value):
            return rule.to_error() or "Does not match required format."

    elif rtype == "email":
        if isinstance(value, str) and "@" not in value:
            return rule.to_error() or "Must be a valid email address."

    elif rtype == "custom":
        name = params.get("name")
        if name and name in _custom_validators:
            fn = _custom_validators[name]
            err = fn(value, params)
            if err:
                return err
        else:
            return f"Unknown custom validator: {name}"

    elif rtype == "one_of":
        allowed = params.get("values", [])
        if value not in allowed:
            return rule.to_error() or f"Must be one of: {allowed}"

    return None


# Example custom validator registration (can be done by user wizards too)
def _example_age_validator(value: Any, params: dict[str, Any]) -> str | None:
    try:
        age = int(value)
        if age < 13:
            return "You must be at least 13 years old to create a profile."
    except (TypeError, ValueError):
        return "Age must be a whole number."
    return None


register_validator("min_age_13", _example_age_validator)
