"""
Per-step validation for wizard input steps.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState
from palm.patterns.wizard.schema_validation import (
    validate_collected_answers_errors,
    validate_flow_schema_key_errors,
    validate_step_schema_errors,
)

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
) -> ValidationResult:
    """Validate ``value`` for an input step."""
    reg = registry or default_validation_registry()
    rules = step.validation
    if not rules:
        return _builtin_field_validation(step, value)
    base = _builtin_field_validation(step, value)
    if not base.ok:
        return base
    return reg.validate(step, value, rules)


def validate_step_state_schema(
    state: BaseState,
    step_slug: str,
    value: Any,
) -> ValidationResult:
    """Validate ``value`` against the bound flow-level schema for ``step_slug``."""
    return _result_from_errors(validate_flow_schema_key_errors(state, step_slug, value))


def validate_step_schema(step: WizardStepConfig, value: Any) -> ValidationResult:
    """Validate ``value`` against the step's own schema when configured."""
    return _result_from_errors(validate_step_schema_errors(step, value))


def validate_collected_answers(
    state: BaseState,
    answers: Mapping[str, Any],
) -> ValidationResult:
    """Validate the full answers mapping against the bound flow-level schema."""
    return _result_from_errors(validate_collected_answers_errors(state, answers))


def validate_step_input(
    state: BaseState,
    step: WizardStepConfig,
    value: Any,
    *,
    registry: ValidationRegistry | None = None,
) -> ValidationResult:
    """Run built-in, declarative, step-schema, and flow-schema validation."""
    result = validate_step_value(step, value, registry=registry)
    if not result.ok:
        return result
    result = validate_step_schema(step, value)
    if not result.ok:
        return result
    return validate_step_state_schema(state, step.slug, value)


def _result_from_errors(errors: list[str]) -> ValidationResult:
    if not errors:
        return ValidationResult.success()
    return ValidationResult.failure(*errors)


def _builtin_field_validation(step: WizardStepConfig, value: Any) -> ValidationResult:
    if step.required and (value is None or value == ""):
        return ValidationResult.failure("Value is required")
    if step.field_type == "choice" and value not in step.choices:
        return ValidationResult.failure(f"Value must be one of {step.choices}")
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
