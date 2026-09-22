"""GraphQL provider app manifest."""

from __future__ import annotations

from palm.common.providers.app import ProviderApp


class GraphqlApp(ProviderApp):
    name = "graphql"
    label = "GraphQL resource access"
    palm_layers = ("core.resource",)
    actions = ("fetch",)
    registry_hooks = ("provider_registry",)


graphql_app = GraphqlApp()

__all__ = ["GraphqlApp", "graphql_app"]
