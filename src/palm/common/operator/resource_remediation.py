"""Remediation hints for resource invocation failures."""

from __future__ import annotations


def resource_invoke_remediation(
    *,
    error: str | None,
    resource_ref: str | None = None,
    provider: str | None = None,
) -> str | None:
    """Return operator-facing remediation text for a resource failure."""
    if not error:
        return None

    lowered = error.lower()
    provider_label = provider or "rest"

    if "base_url" in lowered:
        ref_hint = f"resource_ref={resource_ref!r}" if resource_ref else "resource_ref"
        return (
            f"Set base_url in definition params or palm_providers_invoke params "
            f"(e.g. params={{base_url: http://host:port}}). Invoke {ref_hint} by "
            "definition name from palm://definitions/resources, not palm:// URIs."
        )

    if "definition resolver is not configured" in lowered:
        return "Start ApplicationHost/runtime before invoking resources."

    if "not found" in lowered or "unknown resource" in lowered:
        return (
            "Use a definition name from palm://definitions/resources "
            "(not palm:// URIs). Check palm_system_doctor resource_preflight."
        )

    if "unsupported action" in lowered:
        return (
            f"Check provider actions for {provider_label!r}; "
            "use palm resource describe <ref> or Explorer /explorer/resources."
        )

    if provider == "rest" or "rest fetch" in lowered:
        return (
            "REST resources need base_url and a reachable host. "
            "Run palm_system_doctor() for resource_preflight."
        )

    return None


def enrich_provider_result(result: dict[str, object]) -> dict[str, object]:
    """Attach remediation hint to a provider invoke envelope when invoke failed."""
    if result.get("success"):
        return result

    error = result.get("error")
    metadata = result.get("metadata")
    provider = None
    resource_ref = None
    if isinstance(metadata, dict):
        provider = metadata.get("provider")
        resource_ref = metadata.get("resource_ref") or metadata.get("definition_name")

    hint = resource_invoke_remediation(
        error=str(error) if error is not None else None,
        resource_ref=str(resource_ref) if resource_ref else None,
        provider=str(provider) if provider else None,
    )
    if hint:
        enriched = dict(result)
        enriched["remediation"] = hint
        return enriched
    return result


__all__ = ["enrich_provider_result", "resource_invoke_remediation"]