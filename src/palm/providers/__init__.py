"""
Concrete resource providers — REST, GraphQL, and Postgres (Django-style apps).

Each subpackage registers via its own ``registry.py``.
"""

from palm.providers._apps import INSTALLED_PROVIDERS, autoload

autoload()

from palm.providers import graphql, palm, postgres, rest  # noqa: E402

__all__ = ["INSTALLED_PROVIDERS", "autoload", "graphql", "palm", "postgres", "rest"]
