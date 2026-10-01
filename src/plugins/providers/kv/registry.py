"""KV provider registration. Call :func:`register` with the system registries."""

from palm.system.registries import SystemRegistries
from plugins.providers.kv.provider import KvProvider


def register(registries: SystemRegistries) -> None:
    """Register the kv provider on ``registries``."""
    registries.require("provider").register("kv", KvProvider)


__all__ = ["register"]
