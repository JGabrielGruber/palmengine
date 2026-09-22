"""0.70.1 — plugins.kits.authoring kit-as-composition.

Library door: one object holds host.definitions and walks one-shot commit.
Not an AuthoringService. Not Design. Not land verbs on present.
Handle class stays unnamed.
"""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from palm.definitions.flow import FlowDefinition


def _wizard_body(name: str) -> dict:
    return FlowDefinition(
        name=name,
        pattern="wizard",
        options={"steps": [{"slug": "n", "title": "N", "prompt": "?"}]},
    ).to_dict()


def test_authoring_kit_is_installed() -> None:
    import plugins.kits.authoring as authoring
    from plugins.kits import INSTALLED_KITS, INTENTION_KITS, get_kit, list_kits

    assert authoring is not None
    assert "authoring" in INSTALLED_KITS
    assert INTENTION_KITS == ()
    info = get_kit("authoring")
    assert info is not None
    assert info.module == "plugins.kits.authoring"
    assert "authoring" in {k.name for k in list_kits()}


def test_land_commits_flow_on_embedded_definitions_without_design() -> None:
    from plugins.kits.authoring import land

    host = ApplicationHost.for_mode("test")
    host.start()
    try:
        assert host.design is None
        assert host.assist is None
        assert host.definitions is not None

        kit = land(host)
        published = kit.commit(_wizard_body("authored-thin"))

        assert published["name"] == "authored-thin"
        fetched = host.definitions.get_flow("authored-thin")
        assert fetched["name"] == "authored-thin"
    finally:
        host.shutdown()
