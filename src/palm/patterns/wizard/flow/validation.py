"""
Wizard validation — field rules, schema checks, coercion, and error feedback.

Validation runs in order: built-in field rules → declarative rules → per-step
schema → flow schema. :func:`coerce_step_input` converts CLI string input to
schema-expected types (e.g. ``"27"`` → ``27``) before checks run.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from palm.core.context import BaseState, StateSchema
from palm.core.exceptions import StateValidationError
from palm.patterns.wizard.bindings.context.keys import WizardKeys

if TYPE_CHECKING:
    from palm.patterns.wizard.bindings.definitions.config import WizardStepConfig

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


def format_validation_message(message: str) -> str:
    """Turn a schema or rule message into a short, actionable user message."""
    if message.startswith("missing required key: "):
        field = message.removeprefix("missing required key: ")
        return f"Missing required answer: {field.replace('_', ' ')}"

    minimum_match = re.fullmatch(r"(.+): (.+) < minimum (.+)", message)
    if minimum_match:
        field, value, minimum = minimum_match.groups()
        label = field.replace("_", " ")
        return f"{label} must be at least {minimum} (you entered {value})"

    maximum_match = re.fullmatch(r"(.+): (.+) > maximum (.+)", message)
    if maximum_match:
        field, value, maximum = maximum_match.groups()
        label = field.replace("_", " ")
        return f"{label} must be at most {maximum} (you entered {value})"

    enum_match = re.fullmatch(r"(.+): value (.+) not in enum (.+)", message)
    if enum_match:
        field, value, allowed = enum_match.groups()
        label = field.replace("_", " ")
        return f"{label} must be one of {allowed} (you entered {value})"

    type_match = re.fullmatch(r"(.+): expected (.+), got (.+)", message)
    if type_match:
        field, expected, got = type_match.groups()
        label = field.replace("_", " ")
        return f"{label} must be a {expected} (you entered a {got})"

    return message


def format_validation_messages(errors: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Format every validation message for display."""
    return tuple(format_validation_message(error) for error in errors)


def publish_validation_feedback(
    state: BaseState,
    errors: tuple[str, ...] | list[str],
    *,
    prompt_bundle: dict[str, Any] | None = None,
    prompt_key: str | None = None,
) -> tuple[str, ...]:
    """Write formatted validation feedback into wizard state and optional prompt."""
    formatted = format_validation_messages(errors)
    primary = formatted[0] if formatted else "Please fix the highlighted answers."
    state.set(WizardKeys.VALIDATION_ERROR, primary)
    state.set(WizardKeys.VALIDATION_ERRORS, list(formatted))
    if prompt_bundle is not None:
        bundle = dict(prompt_bundle)
        bundle["validation_error"] = primary
        bundle["validation_errors"] = list(formatted)
        state.set(WizardKeys.ACTIVE_PROMPT, bundle)
        if prompt_key is not None:
            state.set(prompt_key, bundle)
    return formatted


def clear_validation_feedback(state: BaseState) -> None:
    """Remove validation feedback after a successful step transition."""
    state.delete(WizardKeys.VALIDATION_ERROR)
    state.delete(WizardKeys.VALIDATION_ERRORS)
    prompt = state.get(WizardKeys.ACTIVE_PROMPT)
    if isinstance(prompt, dict) and (
        "validation_error" in prompt or "validation_errors" in prompt
    ):
        cleaned = dict(prompt)
        cleaned.pop("validation_error", None)
        cleaned.pop("validation_errors", None)
        state.set(WizardKeys.ACTIVE_PROMPT, cleaned)


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


def validate_step_schema(
    step: WizardStepConfig,
    value: Any,
    *,
    state: BaseState | None = None,
) -> ValidationResult:
    """Validate ``value`` against the step or active scope schema."""
    return _result_from_errors(_validate_step_schema_errors(step, value, state=state))


def validate_step_state_schema(
    state: BaseState,
    step_slug: str,
    value: Any,
) -> ValidationResult:
    """Validate ``value`` against the bound flow-level schema for ``step_slug``."""
    return _result_from_errors(_validate_flow_schema_key_errors(state, step_slug, value))


def validate_collected_answers(
    state: BaseState,
    answers: Mapping[str, Any],
) -> ValidationResult:
    """Validate the full answers mapping against the bound flow-level schema."""
    return _result_from_errors(_validate_collected_answers_errors(state, answers))


def coerce_step_input(
    state: BaseState,
    step: WizardStepConfig,
    value: Any,
) -> Any:
    """Coerce raw user input (often strings from CLI) to schema-expected types."""
    spec = _step_value_schema_spec(state, step)
    if spec is None:
        return value
    return _coerce_value_for_schema(value, spec)


def format_numbered_choices(choices: Sequence[str]) -> str:
    """Format choices as a numbered list for prompts and error messages."""
    return "\n".join(f"{index}. {choice}" for index, choice in enumerate(choices, start=1))


def choice_selection_error(raw: Any, choices: Sequence[str]) -> str:
    """Build a user-facing error when a choice could not be resolved."""
    if not choices:
        return f"Invalid selection: {raw!r}"
    return (
        f"Invalid selection {raw!r}. Enter a number (1-{len(choices)}) "
        f"or matching option name:\n{format_numbered_choices(choices)}"
    )


def resolve_choice_value(value: Any, choices: Sequence[str]) -> str | None:
    """Resolve raw input to a canonical choice value, if possible."""
    if not choices:
        return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text in choices:
            return text

        lowered = text.lower()
        case_insensitive = [choice for choice in choices if choice.lower() == lowered]
        if len(case_insensitive) == 1:
            return case_insensitive[0]

        if text.isdigit():
            index = int(text)
            if 1 <= index <= len(choices):
                return choices[index - 1]

        prefix_matches = [choice for choice in choices if choice.lower().startswith(lowered)]
        if len(prefix_matches) == 1:
            return prefix_matches[0]

        substring_matches = [choice for choice in choices if lowered in choice.lower()]
        if len(substring_matches) == 1:
            return substring_matches[0]

        return None

    if isinstance(value, int) and not isinstance(value, bool):
        if 1 <= value <= len(choices):
            return choices[value - 1]

    if value in choices:
        return str(value)

    return None


def prepare_step_input(
    state: BaseState,
    step: WizardStepConfig,
    value: Any,
) -> tuple[Any, ValidationResult | None]:
    """Resolve choice aliases and coerce raw input before validation."""
    if step.field_type == "choice" and step.choices:
        resolved = resolve_choice_value(value, step.choices)
        if resolved is None:
            return value, ValidationResult.failure(choice_selection_error(value, step.choices))
        value = resolved
    value = coerce_step_input(state, step, value)
    return value, None


def validate_prepared_step_input(
    state: BaseState,
    step: WizardStepConfig,
    value: Any,
    *,
    registry: ValidationRegistry | None = None,
) -> ValidationResult:
    """Validate input that has already been resolved and coerced."""
    result = validate_step_value(step, value, registry=registry)
    if not result.ok:
        return _result_from_errors(format_validation_messages(result.errors))
    result = validate_step_schema(step, value, state=state)
    if not result.ok:
        return _result_from_errors(format_validation_messages(result.errors))
    result = validate_step_state_schema(state, step.slug, value)
    if not result.ok:
        return _result_from_errors(format_validation_messages(result.errors))
    return result


def validate_step_input(
    state: BaseState,
    step: WizardStepConfig,
    value: Any,
    *,
    registry: ValidationRegistry | None = None,
) -> ValidationResult:
    """Run built-in, declarative, step-schema, and flow-schema validation."""
    value, choice_error = prepare_step_input(state, step, value)
    if choice_error is not None:
        return choice_error
    return validate_prepared_step_input(state, step, value, registry=registry)


def _validate_schema_value(schema: StateSchema, value: Any, *, path: str) -> list[str]:
    return schema.validate_value(value, path=path)


def _step_value_schema_spec(
    state: BaseState,
    step: WizardStepConfig,
) -> dict[str, Any] | None:
    if step.schema is not None:
        definition = step.schema.definition
        if isinstance(definition, dict):
            return definition
    if step.state_schema is not None:
        return dict(step.state_schema)
    if state is not None:
        scope_schema = state.scope_schemas().get(step.slug)
        if scope_schema is not None:
            definition = scope_schema.definition
            if isinstance(definition, dict):
                return definition
        flow_schema = state.schema
        if flow_schema is not None:
            flow_definition = flow_schema.definition
            if not isinstance(flow_definition, dict):
                return None
            properties = flow_definition.get("properties", {})
            if isinstance(properties, dict):
                property_spec = properties.get(step.slug)
                if isinstance(property_spec, dict):
                    return property_spec
    return None


def _coerce_value_for_schema(value: Any, spec: Mapping[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    if stripped == "":
        return value

    expected_type = spec.get("type")
    if expected_type == "integer":
        coerced = _coerce_string_to_integer(stripped)
        return coerced if coerced is not None else value
    if expected_type == "number":
        try:
            return float(stripped)
        except ValueError:
            return value
    if expected_type == "boolean":
        lowered = stripped.lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return value


def _coerce_string_to_integer(text: str) -> int | None:
    try:
        if "." in text or "e" in text.lower():
            parsed = float(text)
            if parsed.is_integer():
                return int(parsed)
            return None
        return int(text)
    except ValueError:
        return None


def _validate_step_schema_errors(
    step: WizardStepConfig,
    value: Any,
    *,
    state: BaseState | None = None,
) -> list[str]:
    schema = step.schema
    if schema is None and state is not None:
        schema = state.scope_schemas().get(step.slug)
    if schema is None:
        return []
    return _validate_schema_value(schema, value, path=step.slug)


def _validate_flow_schema_key_errors(
    state: BaseState,
    step_slug: str,
    value: Any,
) -> list[str]:
    schema = state.schema
    if schema is None:
        return []
    try:
        schema.validate_key(step_slug, value)
    except StateValidationError as exc:
        return [str(exc)]
    return []


def _validate_collected_answers_errors(
    state: BaseState,
    answers: Mapping[str, Any],
) -> list[str]:
    schema = state.schema
    if schema is None:
        return []
    return schema.validate_state(dict(answers))


def _result_from_errors(errors: list[str] | tuple[str, ...]) -> ValidationResult:
    if not errors:
        return ValidationResult.success()
    return ValidationResult.failure(*errors)


def _builtin_field_validation(step: WizardStepConfig, value: Any) -> ValidationResult:
    if step.required and (value is None or value == ""):
        return ValidationResult.failure("This field is required")
    if step.field_type == "choice" and value not in step.choices:
        return ValidationResult.failure(choice_selection_error(value, step.choices))
    if step.field_type == "confirm":
        allowed = {True, False, "yes", "no", "Yes", "No"}
        if value not in allowed:
            return ValidationResult.failure("Please answer yes or no")
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
            return ValidationResult.failure(f"Enter at least {minimum} characters")
        return ValidationResult.success()

    if name == "max_length":
        maximum = int(params.get("max", 10_000))
        if len(str(value)) > maximum:
            return ValidationResult.failure(f"Enter at most {maximum} characters")
        return ValidationResult.success()

    if name == "regex":
        pattern = str(params.get("pattern", ""))
        if pattern:
            candidate = "" if value is None else str(value)
            if not re.search(pattern, candidate):
                return ValidationResult.failure(
                    params.get("message", "Value does not match the required pattern")
                )
        return ValidationResult.success()

    if name == "not_empty":
        if value is None or str(value).strip() == "":
            return ValidationResult.failure("This field cannot be empty")
        return ValidationResult.success()

    return ValidationResult.failure(f"Unknown validation rule: {name!r}")


_default_registry = ValidationRegistry()


def default_validation_registry() -> ValidationRegistry:
    return _default_registry
