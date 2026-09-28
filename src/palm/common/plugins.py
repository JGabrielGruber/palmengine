"""Plugin package side-effect registration (shared bootstrap helper).

System code must not import ``palm.patterns`` / product surfaces
(``scripts/guard_system.py``). The standard bundle calls this function from
kernel bootstrap, before system start. The system schedule does not install.

**0.72.3:** the function takes the package names from a composition record.
It does not keep a process flag, and it does not close over ``INSTALLED_*``.
A later call imports names that are not yet imported. It does not unload
names already imported.

**0.72.4:** transform names are on that same record. Service packages stay
on the host phenotype (``CompositionProfile.services``). This stroke does
not import them.
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
    """Import the named plugin packages and register the named transform rules."""
    from plugins.kits import autoload as autoload_kits
    from plugins.patterns import autoload as autoload_patterns
    from plugins.providers import autoload as autoload_providers
    from drivers.runners import autoload as autoload_runners
    from drivers.storages import autoload as autoload_storages

    from palm.common.transforms import autoload as autoload_transforms

    autoload_kits(tuple(kits))
    autoload_patterns(tuple(patterns))
    autoload_providers(tuple(providers))
    autoload_runners(tuple(runners))
    autoload_storages(tuple(storages))
    autoload_transforms(tuple(transforms))
