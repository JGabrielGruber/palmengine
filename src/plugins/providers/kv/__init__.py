"""KV resource provider package.

Importing this package does not register the provider.
Call :func:`plugins.providers.kv.registry.register`.
"""

from plugins.providers.kv.provider import KvProvider

__all__ = ["KvProvider"]