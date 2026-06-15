"""
State schema contracts — validation and defaults for execution state.

Provides a lightweight JSON Schema-inspired subset for dict-based dynamic flows
without external validation dependencies. All logic stays inside ``palm.core``.

Typical usage::

    schema = DictStateSchema({
        "type": "object",
        "properties": {"age": {"type": "integer", "minimum": 18}},
        "required": ["age"],
    })
    schema.validate_key("age", 25)   # ok
    schema.validate_state({"age": 16})  # ["age: 16 < minimum 18"]

Flow and wizard layers bind schemas at submission time; wizards may also bind
per-step schemas to named scopes for immediate input validation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from palm.core.exceptions import StateValidationError

_TYPE_CHECKS: dict[str, Any] = {
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, int | float) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "array": lambda value: isinstance(value, list),
    "object": lambda value: isinstance(value, dict),
    "null": lambda value: value is None,
}


class StateSchema(ABC):
    """Abstract contract for validating and defaulting execution state."""

    @property
    def definition(self) -> dict[str, Any] | None:
        """Return a serializable schema document when available."""
        return None

    @abstractmethod
    def validate_key(self, key: str, value: Any) -> None:
        """Validate ``value`` for ``key``. Raise ``StateValidationError`` on failure."""

    @abstractmethod
    def validate_state(self, state: Mapping[str, Any]) -> list[str]:
        """Validate a full state mapping. Return human-readable error messages."""

    @abstractmethod
    def validate_value(self, value: Any, *, path: str = "value") -> list[str]:
        """Validate a single value against the root schema document."""

    @abstractmethod
    def defaults(self) -> dict[str, Any]:
        """Return default values declared by the schema."""


class DictStateSchema(StateSchema):
    """JSON Schema-style dict schema with a built-in subset validator.

    Supports root ``type: object`` documents with ``properties``, ``required``,
    per-property ``type``, ``default``, ``enum``, ``minimum``/``maximum``,
    ``minLength``/``maxLength``, ``minItems``/``maxItems``, and nested
    ``object``/``array`` ``items`` definitions.
    """

    def __init__(self, definition: Mapping[str, Any]) -> None:
        self._definition = dict(definition)

    @property
    def definition(self) -> dict[str, Any]:
        """Return a shallow copy of the underlying schema document."""
        return dict(self._definition)

    def validate_key(self, key: str, value: Any) -> None:
        properties = self._properties()
        if key not in properties:
            return
        errors = _validate_value(value, properties[key], path=key)
        if errors:
            raise StateValidationError(errors[0])

    def validate_state(self, state: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        properties = self._properties()
        required = self._required()

        for key in required:
            if key not in state:
                errors.append(f"missing required key: {key}")

        for key, value in state.items():
            if key not in properties:
                continue
            errors.extend(_validate_value(value, properties[key], path=key))

        return errors

    def validate_value(self, value: Any, *, path: str = "value") -> list[str]:
        return _validate_value(value, self._definition, path=path)

    def defaults(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, spec in self._properties().items():
            if "default" in spec:
                result[key] = spec["default"]
        return result

    def _properties(self) -> dict[str, Any]:
        root_type = self._definition.get("type", "object")
        if root_type != "object":
            return {}
        properties = self._definition.get("properties")
        if not isinstance(properties, dict):
            return {}
        return properties

    def _required(self) -> list[str]:
        required = self._definition.get("required", [])
        if not isinstance(required, list):
            return []
        return [str(key) for key in required]


def _validate_value(value: Any, spec: Mapping[str, Any], *, path: str) -> list[str]:
    errors: list[str] = []
    expected_type = spec.get("type")
    if expected_type is not None:
        if not _matches_type(value, expected_type):
            errors.append(
                f"{path}: expected {expected_type}, got {type(value).__name__}",
            )
            return errors

    if "enum" in spec:
        allowed = spec["enum"]
        if isinstance(allowed, list) and value not in allowed:
            errors.append(f"{path}: value {value!r} not in enum {allowed!r}")

    if isinstance(expected_type, list):
        return errors

    if expected_type in {"integer", "number"}:
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"{path}: {value} < minimum {spec['minimum']}")
        if "maximum" in spec and value > spec["maximum"]:
            errors.append(f"{path}: {value} > maximum {spec['maximum']}")

    if expected_type == "string":
        if "minLength" in spec and len(value) < spec["minLength"]:
            errors.append(
                f"{path}: length {len(value)} < minLength {spec['minLength']}",
            )
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            errors.append(
                f"{path}: length {len(value)} > maxLength {spec['maxLength']}",
            )

    if expected_type == "object":
        properties = spec.get("properties", {})
        required = spec.get("required", [])
        if isinstance(properties, dict) and isinstance(value, dict):
            if isinstance(required, list):
                for key in required:
                    if key not in value:
                        errors.append(f"{path}.{key}: missing required key")
            for key, nested_value in value.items():
                nested_spec = properties.get(key)
                if isinstance(nested_spec, dict):
                    errors.extend(
                        _validate_value(nested_value, nested_spec, path=f"{path}.{key}"),
                    )

    if expected_type == "array":
        if isinstance(value, list):
            if "minItems" in spec and len(value) < spec["minItems"]:
                errors.append(
                    f"{path}: length {len(value)} < minItems {spec['minItems']}",
                )
            if "maxItems" in spec and len(value) > spec["maxItems"]:
                errors.append(
                    f"{path}: length {len(value)} > maxItems {spec['maxItems']}",
                )
        items = spec.get("items")
        if isinstance(items, dict) and isinstance(value, list):
            for index, item in enumerate(value):
                errors.extend(
                    _validate_value(item, items, path=f"{path}[{index}]"),
                )

    return errors


def _matches_type(value: Any, expected_type: str | list[str]) -> bool:
    if isinstance(expected_type, list):
        return any(_matches_type(value, item) for item in expected_type)
    checker = _TYPE_CHECKS.get(expected_type)
    if checker is None:
        return True
    return bool(checker(value))
