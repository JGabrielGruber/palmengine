"""Graphql provider registration."""

from palm.core.registry import provider_registry
from palm.providers.graphql.provider import GraphqlProvider

provider_registry.register("graphql", GraphqlProvider)
