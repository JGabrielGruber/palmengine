"""
Palm kits — shared surface infrastructure, exposed by name.

Kits are **not** the system layer and **not** product services.
They hold reusable transport and presentation glue (HTTP protocol, routes,
SSR helpers, …) so runtimes stay thin adapters.

Law (SD-011 / 0.57.13):

- One implementation per kit (no dual trees).
- Named home: ``palm.kits.<name>`` — not anonymous bulk under ``common``.
- Install list is truth: :data:`INSTALLED_KITS`.
- Surfaces import kits; they do not invent private protocol copies.

Import the server kit as :mod:`palm.kits.server`.
Import the present kit as :mod:`palm.kits.present` (0.69.4 / 0.69.5).
Import the authoring kit as :mod:`palm.kits.authoring` (0.70.1).

Core kits (``present``, ``authoring``) populate via :func:`autoload` at
bootstrap (:func:`palm.common.plugins.ensure_core_plugins`). Surface kit
``server`` registers when the server runtime imports it (0.71.21).
"""

from __future__ import annotations

from palm.kits._apps import CORE_KITS, INSTALLED_KITS, INTENTION_KITS, autoload
from palm.kits.registry import (
    KitInfo,
    clear_kits,
    get_kit,
    installed_kit_names,
    list_kits,
    register_kit,
)

__all__ = [
    "CORE_KITS",
    "INSTALLED_KITS",
    "INTENTION_KITS",
    "KitInfo",
    "autoload",
    "clear_kits",
    "get_kit",
    "installed_kit_names",
    "list_kits",
    "register_kit",
]
