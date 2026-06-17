"""Palm Explorer layout — branded shell over shared SSR helpers."""

from __future__ import annotations

from palm.common.runtimes.server.ssr.layout import page_shell

_EXPLORER_NAV = (
    ("Home", "/explorer"),
    ("Flows", "/explorer/flows"),
    ("Processes", "/explorer/processes"),
    ("Patterns", "/explorer/patterns"),
    ("Schemas", "/explorer/schemas"),
    ("Jobs", "/explorer/jobs"),
    ("Instances", "/explorer/instances"),
    ("API Reference", "/v1/docs"),
    ("Examples", "/explorer/examples"),
)

_FOOTER_PILLS = (("Health", "/health"), ("OpenAPI", "/v1/openapi.json"))


def explorer_page(
    *,
    title: str,
    version: str,
    content: str,
    active_nav: str = "/explorer",
    subtitle: str = "",
) -> str:
    """Wrap page content in the Palm Explorer layout."""
    return page_shell(
        title=title,
        brand="Palm Explorer",
        version=version,
        content=content,
        nav=_EXPLORER_NAV,
        active_nav=active_nav,
        subtitle=subtitle,
        footer_pills=_FOOTER_PILLS,
    )


def wiki_page(
    *,
    title: str,
    version: str,
    content: str,
    active_nav: str = "/explorer",
    subtitle: str = "",
) -> str:
    """Backward-compatible alias for :func:`explorer_page`."""
    return explorer_page(
        title=title,
        version=version,
        content=content,
        active_nav=active_nav,
        subtitle=subtitle,
    )