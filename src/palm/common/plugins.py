"""Plugin package side-effect registration (shared bootstrap helper).

System code must not import ``palm.patterns`` / product surfaces
(``scripts/guard_system.py``). Call :func:`ensure_core_plugins` from
system-instance start so registries populate without the system layer
depending on plugin packages at import time.
"""

from __future__ import annotations

_loaded = False


def ensure_core_plugins() -> None:
    """Call plugin ``autoload`` so registries are populated at bootstrap.

    Safe to call multiple times. Used by system runtime start and app bootstrap.
    Package import alone does not load ``INSTALLED_*`` members.
    """
    global _loaded
    if _loaded:
        return
    import palm.common.transforms  # noqa: F401 — common transform rules
    from palm.kits import autoload as autoload_kits
    from palm.patterns import autoload as autoload_patterns
    from palm.providers import autoload as autoload_providers
    from palm.runners import autoload as autoload_runners
    from palm.storages import autoload as autoload_storages

    autoload_kits()
    autoload_patterns()
    autoload_providers()
    autoload_runners()
    autoload_storages()

    _loaded = True
