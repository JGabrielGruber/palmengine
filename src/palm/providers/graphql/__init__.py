"""Graphql provider app."""

from palm.providers.graphql import registry as registry
from palm.providers.graphql.provider import GraphqlProvider

__all__ = ["GraphqlProvider", "registry"]
