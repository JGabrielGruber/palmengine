"""
Per-step validation for wizard input steps.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.patterns.wizard.config import WizardStepConfig

ValidatorFunc = Callable[[Any, "WizardStepConfig"], str | None]


@dataclass(frozen=True)
class StepValidationRule:
    """Declarative validation rule (serializable from definitions)."""

    rule: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()

    @staticmethod
    def success() -> ValidationResult:
        return ValidationResult(ok=True)

    @staticmethod
    def failure(*messages: str) -> ValidationResult:
        return ValidationResult(ok=False, errors=messages)


class ValidationRegistry:
    """Register named validators for definition-driven wizards."""

    def __init__(self) -> None:
        self._custom: dict[str, ValidatorFunc] = {}

    def register(self, name: str, validator: ValidatorFunc) -> None:
        self._custom[name] = validator

    def validate(
        self,
        step: WizardStepConfig,
        value: Any,
        rules: tuple[StepValidationRule, ...],
    ) -> ValidationResult:
        errors: list[str] = []
        for rule in rules:
            result = _run_rule(rule, step, value, self._custom)
            if not result.ok:
                errors.extend(result.errors)
        return ValidationResult(ok=not errors, errors=tuple(errors))


def validate_step_value(
    step: WizardStepConfig,
    value: Any,
    *,
    registry: ValidationRegistry | None = None,
    choices: tuple[str, ...] | None = None,
) -> ValidationResult:
    """Validate ``value`` for an input step."""
    reg = registry or default_validation_registry()
    rules = step.validation
    if not rules:
        return _builtin_field_validation(step, value, choices=choices)
    base = _builtin_field_validation(step, value, choices=choices)
    if not base.ok:
        return base
    return reg.validate(step, value, rules)


def _builtin_field_validation(
    step: WizardStepConfig,
    value: Any,
    *,
    choices: tuple[str, ...] | None = None,
) -> ValidationResult:
    if step.required and (value is None or value == ""):
        return ValidationResult.failure("Value is required")
    if step.field_type == "choice":
        allowed = choices if choices is not None else step.choices
        if allowed and value not in allowed:
            return ValidationResult.failure(f"Value must be one of {allowed}")
    if step.field_type == "confirm":
        allowed = {True, False, "yes", "no", "Yes", "No"}
        if value not in allowed:
            return ValidationResult.failure("Confirmation must be yes or no")
    return ValidationResult.success()


def _run_rule(
    rule: StepValidationRule,
    step: WizardStepConfig,
    value: Any,
    custom: dict[str, ValidatorFunc],
) -> ValidationResult:
    name = rule.rule
    params = rule.params

    if name in custom:
        message = custom[name](value, step)
        if message:
            return ValidationResult.failure(message)
        return ValidationResult.success()

    if name == "min_length":
        minimum = int(params.get("min", 1))
        if len(str(value)) < minimum:
            return ValidationResult.failure(f"Minimum length is {minimum}")
        return ValidationResult.success()

    if name == "max_length":
        maximum = int(params.get("max", 10_000))
        if len(str(value)) > maximum:
            return ValidationResult.failure(f"Maximum length is {maximum}")
        return ValidationResult.success()

    if name == "regex":
        pattern = str(params.get("pattern", ""))
        if pattern and not re.search(pattern, str(value)):
            return ValidationResult.failure(params.get("message", "Value does not match pattern"))
        return ValidationResult.success()

    if name == "not_empty":
        if value is None or str(value).strip() == "":
            return ValidationResult.failure("Value must not be empty")
        return ValidationResult.success()

    return ValidationResult.failure(f"Unknown validation rule: {name!r}")


_default_registry = ValidationRegistry()


def default_validation_registry() -> ValidationRegistry:
    return _default_registry
