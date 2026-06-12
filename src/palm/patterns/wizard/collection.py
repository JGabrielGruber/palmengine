"""
Collection step configuration — repeatable item fields for wizard flows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from palm.common.exceptions import DefinitionBuildError
from palm.patterns.wizard.validation import StepValidationRule

CollectionFieldType = Literal["text", "choice", "confirm"]

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.core.context import StateSchema


@dataclass(frozen=True)
class CollectionFieldConfig:
    """One field collected for each item in a collection step."""

    slug: str
    title: str
    prompt: str
    field_type: CollectionFieldType = "text"
    choices: tuple[str, ...] = ()
    required: bool = True
    validation: tuple[StepValidationRule, ...] = ()
    state_schema: dict[str, Any] | None = None
    state_schema_ref: str | None = None
    schema: StateSchema | None = None

    def materialize_state_schema(
        self,
        repository: DefinitionRepository | None = None,
    ) -> StateSchema | None:
        if self.schema is not None:
            return self.schema
        from palm.common.state.schema_binding import materialize_state_schema

        return materialize_state_schema(
            inline=self.state_schema,
            ref=self.state_schema_ref,
            repository=repository,
        )


def item_fields_from_mapping(
    raw: Any,
    *,
    repository: DefinitionRepository | None = None,
) -> tuple[CollectionFieldConfig, ...]:
    """Parse ``item_fields`` from a collection step definition."""
    if not isinstance(raw, list) or not raw:
        raise DefinitionBuildError("Collection step requires a non-empty 'item_fields' list")

    fields: list[CollectionFieldConfig] = []
    for item in raw:
        if not isinstance(item, dict):
            raise DefinitionBuildError("Each collection item_field must be a mapping")
        slug = item.get("slug")
        if not slug:
            raise DefinitionBuildError("Collection item_field requires 'slug'")

        field_type = item.get("field_type", "text")
        if field_type not in {"text", "choice", "confirm"}:
            raise DefinitionBuildError(f"Invalid collection field_type: {field_type!r}")

        choices = item.get("choices", ())
        if isinstance(choices, list):
            choices = tuple(choices)

        validation_raw = item.get("validation", ())
        validation: tuple[StepValidationRule, ...] = ()
        if isinstance(validation_raw, list):
            validation = tuple(
                StepValidationRule(
                    rule=str(rule["rule"]),
                    params=dict(rule.get("params") or {}),
                )
                for rule in validation_raw
                if isinstance(rule, dict) and "rule" in rule
            )

        inline_schema = item.get("state_schema")
        state_schema = dict(inline_schema) if isinstance(inline_schema, dict) else None
        ref = item.get("state_schema_ref")
        state_schema_ref = str(ref) if ref else None

        field = CollectionFieldConfig(
            slug=str(slug),
            title=str(item.get("title", str(slug).replace("_", " ").title())),
            prompt=str(item.get("prompt", f"Enter {slug}")),
            field_type=field_type,
            choices=choices,
            required=bool(item.get("required", True)),
            validation=validation,
            state_schema=state_schema,
            state_schema_ref=state_schema_ref,
        )
        schema = field.materialize_state_schema(repository)
        if schema is not None:
            field = CollectionFieldConfig(
                slug=field.slug,
                title=field.title,
                prompt=field.prompt,
                field_type=field.field_type,
                choices=field.choices,
                required=field.required,
                validation=field.validation,
                state_schema=field.state_schema,
                state_schema_ref=field.state_schema_ref,
                schema=schema,
            )
        fields.append(field)
    return tuple(fields)
