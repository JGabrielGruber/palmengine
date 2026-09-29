"""Withdrawn catalog install.

The standard bundle used to call this from kernel bootstrap. A plugin registers
when its module is imported. This function does not import one.
"""

from __future__ import annotations


def ensure_core_plugins(
    *,
    kits: tuple[str, ...],
    patterns: tuple[str, ...],
    providers: tuple[str, ...],
    runners: tuple[str, ...],
    storages: tuple[str, ...],
    transforms: tuple[str, ...],
) -> None:
    """Refuse the catalog install stroke."""
    _ = (kits, patterns, providers, runners, storages, transforms)
    raise RuntimeError(
        "catalog install is withdrawn; import the module that registers the plugin"
    )
