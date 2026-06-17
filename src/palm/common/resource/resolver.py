"""
Bridge ``DefinitionRepository`` resources to core ``ResolvedResourceSpec``.
"""

from __future__ import annotations

from collections.abc import Callable

from palm.common.exceptions import DefinitionNotFoundError
from palm.common.persistence.definition_repository import DefinitionRepository
from palm.core.resource.exceptions import ResourceResolutionError
from palm.core.resource.invocation import ResolvedResourceSpec


def resource_definition_resolver(
    repository: DefinitionRepository,
) -> Callable[[str], ResolvedResourceSpec]:
    """Build a resolver callable for :class:`~palm.core.resource.ResourceEngine`."""

    def resolve(ref: str) -> ResolvedResourceSpec:
        try:
            definition = repository.get_resource(ref)
        except DefinitionNotFoundError:
            try:
                definition = repository.get_resource(ref, by_id=True)
            except DefinitionNotFoundError as exc:
                raise ResourceResolutionError(f"Resource not found: {ref}") from exc
        return ResolvedResourceSpec(
            definition_id=definition.definition_id,
            name=definition.name,
            provider=definition.provider,
            action=definition.action,
            resource_id=definition.resource_id,
            params=dict(definition.params),
            output_key=definition.output_key,
        )

    return resolve
