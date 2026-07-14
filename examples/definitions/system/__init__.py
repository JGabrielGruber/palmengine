"""
System ops datasets via the Palm provider.

Registration order:
  1. local resources (``palm-system-*``)
  2. optional origin resources when ``PALM_ORIGIN_URL`` is set
  3. dashboards (local + optional origin)

Remote Palm is a **resource** (``params.remote_url`` on the definition),
not an analytics query param.
"""

from __future__ import annotations

from . import dashboard, origin_dashboard, origin_resources, resources

__all__ = [
    "dashboard",
    "origin_dashboard",
    "origin_resources",
    "resources",
    "register_definitions",
]


def register_definitions(repository: object) -> None:
    resources.register_definitions(repository)
    origin_names = origin_resources.register_origin_from_env(repository)
    dashboard.register_definitions(repository)
    if origin_names:
        # Mirror dashboard for env-registered origin datasets
        import os

        url = (os.environ.get("PALM_ORIGIN_URL") or "").strip()
        prefix = (os.environ.get("PALM_ORIGIN_PREFIX") or "origin").strip() or "origin"
        origin_dashboard.register_origin_system_dashboard(
            name_prefix=prefix,
            remote_url=url or None,
        )
