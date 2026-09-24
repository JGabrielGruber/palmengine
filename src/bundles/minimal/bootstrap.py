"""Install the modules a minimal app names.

The system schedule calls the callable the app passes as ``plugin_install``.
This module performs that import. Registration is each module's own side effect.
"""

from __future__ import annotations

import importlib

#: Storage backend the minimal start selects. The app installs this module.
MEMORY_STORAGE = "plugins.storages.memory"


def install_modules(modules: tuple[str, ...]) -> None:
    """Import each module name in order."""
    for module in modules:
        name = module.strip()
        if not name:
            raise ValueError("plugin module name is empty")
        importlib.import_module(name)
