"""KV provider registration. Call :func:`register` to wire the provider."""

from palm.core.registry import provider_registry
from plugins.providers.kv.app import kv_app
from plugins.providers.kv.provider import KvProvider


def register() -> None:
    """Register the kv provider and the kv app."""
    provider_registry.register("kv", KvProvider)
    kv_app.register()


__all__ = ["register"]
