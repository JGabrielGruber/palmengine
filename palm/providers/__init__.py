"""
Concrete resource providers — REST, GraphQL, and Postgres.

Import submodules to register providers with ``provider_registry``.
"""

from palm.providers import graphql, postgres, rest

__all__ = ["rest", "graphql", "postgres"]
