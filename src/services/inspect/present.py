"""Present system vitality for surfaces (product door).

Law (ADR-030 / VISION-0.61): truth lives in ``palm.system.vitality``.
Product **reads** ``project`` / ``project_top`` / ``run_benchmark`` and shapes
operate envelopes. Does not invent seat counters or a second observation home.

0.61.6 / OD-001: legacy ``doctor`` is **anatomy packaging** only. Living eyes
are :func:`present_top` / :func:`present_vitality`. Doctor may nest those;
it must not invent living seat law.

0.61.11: :func:`present_benchmark` — product door for the vitality **tool**
(opt-in thrash). System owns recipe + diff; product only presents.
"""

from __future__ import annotations

from typing import Any

from palm.system.vitality import (
    CAPABILITY_BENCHMARK,
    DEFAULT_ITERATIONS,
    DEFAULT_RECIPE,
    ProjectionOptions,
    project,
    project_top,
    run_benchmark,
)

# Provenance tag for product envelopes that nest projection.
SOURCE_VITALITY = "palm.system.vitality"

# Demoted doctor envelope (OD-001).
DOCTOR_KIND = "legacy_doctor"
DOCTOR_ROLE = "anatomy_packaging"
OPERATE_EYES_PATHS = (
    "inspect/top",
    "inspect/vitality",
    "inspect/benchmark",
    "assist/top",
    "assist/vitality",
)

BENCHMARK_KIND = "benchmark_present"
BENCHMARK_ROLE = "tool_present"

DOCTOR_DEMOTE_NOTE = (
    "Living physiology is system vitality (inspect top / vitality). "
    "Doctor is legacy anatomy packaging — storage, registries, job counts — "
    "not seat law. Prefer operate_paths for eyes."
)


def _admission_present(instance: Any) -> dict[str, Any] | None:
    """Nest living admission on operate envelopes (not a soft dual)."""
    snap = getattr(instance, "admission", None)
    if snap is None:
        return None
    from palm.system.structure.errors import admission_as_dict

    return admission_as_dict(snap)


def present_top(
    instance: Any,
    options: ProjectionOptions | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Living ``top`` view — structural fold from vitality projection only."""
    top = project_top(instance, options, **kwargs)
    # Product envelope: mark source without rewriting system fields.
    if isinstance(top, dict) and "source" not in top:
        top = {**top, "source": SOURCE_VITALITY}
    if isinstance(top, dict):
        adm = _admission_present(instance)
        if adm is not None and "admission" not in top:
            top = {**top, "admission": adm}
    return top


def present_vitality(
    instance: Any,
    options: ProjectionOptions | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Full vitality snapshot dict from projection only."""
    snap = project(instance, options, **kwargs)
    body = snap.to_dict()
    body["source"] = SOURCE_VITALITY
    adm = _admission_present(instance)
    if adm is not None and "admission" not in body:
        body["admission"] = adm
    return body


def present_benchmark(
    instance: Any,
    *,
    recipe: str = DEFAULT_RECIPE,
    iterations: int = DEFAULT_ITERATIONS,
    mode: str | None = None,
    store_full_snapshots: bool = False,
) -> dict[str, Any]:
    """Present vitality benchmark tool — opt-in; does not invent metrics.

    Calls :func:`~palm.system.vitality.run_benchmark` and wraps the fragment
    in a product envelope (source / kind / role). Surfaces must not thrash
    outside this door or re-measure process/seats privately.
    """
    frag = run_benchmark(
        instance,
        recipe=recipe,
        iterations=iterations,
        mode=mode,
        store_full_snapshots=store_full_snapshots,
    )
    data = dict(frag.data or {})
    envelope: dict[str, Any] = {
        "source": SOURCE_VITALITY,
        "kind": BENCHMARK_KIND,
        "role": BENCHMARK_ROLE,
        "eyes_law": SOURCE_VITALITY,
        "capability_id": CAPABILITY_BENCHMARK,
        "present": frag.present,
        "state": frag.state,
        "notes": list(frag.notes),
        "recipe": data.get("recipe"),
        "iterations": data.get("iterations"),
        "recipe_meta": data.get("recipe_meta"),
        "summary": data.get("summary"),
        "before": data.get("before"),
        "after": data.get("after"),
        "diff": data.get("diff"),
        "timing": data.get("timing"),
        "known_recipes": data.get("known_recipes"),
        "sample_ts": data.get("sample_ts"),
    }
    if store_full_snapshots:
        envelope["before_snapshot"] = data.get("before_snapshot")
        envelope["after_snapshot"] = data.get("after_snapshot")
    if frag.state != "ok":
        envelope["error_notes"] = list(frag.notes)
    return envelope


def present_vitality_for_doctor(top: dict[str, Any]) -> dict[str, Any]:
    """Thin vitality pointer nested under legacy doctor (OD-001)."""
    return {
        "source": SOURCE_VITALITY,
        "schema": top.get("schema"),
        "sample_ts": top.get("sample_ts"),
        "summary": dict(top.get("summary") or {}),
        "note": DOCTOR_DEMOTE_NOTE,
    }


def present_doctor(
    anatomy: dict[str, Any],
    *,
    top: dict[str, Any] | None = None,
    vitality: dict[str, Any] | None = None,
    top_error: str | None = None,
) -> dict[str, Any]:
    """Demote anatomy packaging under a legacy doctor envelope.

    Flat packaging keys from ``anatomy`` stay for consumers (storage, jobs,
    registries, issues, …). Living eyes are explicit: ``top`` / ``vitality``
    plus ``kind`` / ``role`` / ``eyes_law`` / ``operate_paths``.

    Does **not** invent seat counters — those live in projection only.
    """
    report = dict(anatomy)
    report["kind"] = DOCTOR_KIND
    report["role"] = DOCTOR_ROLE
    report["eyes_law"] = SOURCE_VITALITY
    report["operate_paths"] = list(OPERATE_EYES_PATHS)
    report["note"] = DOCTOR_DEMOTE_NOTE

    if top is not None:
        report["top"] = top
    elif top_error is not None:
        report["top"] = {"error": top_error, "source": SOURCE_VITALITY}

    if vitality is not None:
        report["vitality"] = vitality
    elif top is not None:
        report["vitality"] = present_vitality_for_doctor(top)
    elif top_error is not None:
        report["vitality"] = {
            "source": SOURCE_VITALITY,
            "error": top_error,
            "note": (
                "Projection sample failed; anatomy packaging still returned. " + DOCTOR_DEMOTE_NOTE
            ),
        }

    # Nested residual bag (honest structure; flat keys remain for compat).
    packaging_keys = (
        "status",
        "version",
        "runtime",
        "auth_enforce",
        "storage",
        "registries",
        "resource_count",
        "resource_preflight",
        "workloads",
        "control_plane",
        "jobs",
        "reactive_interests",
        "issues",
    )
    anatomy_bag = {k: report[k] for k in packaging_keys if k in report}
    if anatomy_bag:
        report["anatomy"] = anatomy_bag

    return report


__all__ = [
    "SOURCE_VITALITY",
    "DOCTOR_KIND",
    "DOCTOR_ROLE",
    "BENCHMARK_KIND",
    "BENCHMARK_ROLE",
    "OPERATE_EYES_PATHS",
    "DOCTOR_DEMOTE_NOTE",
    "present_top",
    "present_vitality",
    "present_benchmark",
    "present_vitality_for_doctor",
    "present_doctor",
]
