"""Graphql provider app."""

from plugins.providers.graphql import registry as registry
from plugins.providers.graphql.provider import GraphqlProvider

__all__ = ["GraphqlProvider", "registry"]
