"""
Example definition packs.

**Preferred:** multi-file packages under this directory, e.g.::

    examples/definitions/coconut/
        __init__.py      # ordered register_definitions()
        resources.py
        npc.py

Bootstrap loads each package's ``register_definitions`` (then flat ``*.py`` demos).
Order inside a package is owned by that package's ``__init__.py``.
"""
