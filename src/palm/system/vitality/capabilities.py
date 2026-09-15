"""
Default vitality capabilities (0.61.2+).

**Installed observe:** ``seat_walk`` · ``emission_window`` ·
``process_resources`` · ``loaded_bulk``.  
**Installed tool (off by default):** ``benchmark`` (0.61.10).  
Other catalog ids may exist as intention stubs (disabled) so the registry
shape is honest about growth without fake-green bodies.

**Law:** capabilities *receive* seat reports / existing rings; they do not
re-curate doctor fields or invent a second write path for the same fact.
"""

from __future__ import annotations

from typing import Any

from palm.system.vitality.benchmark import sample_benchmark
from palm.system.vitality.capability import (
    CapabilityFragment,
    SampleContext,
    VitalityCapability,
    intention_stub,
)
from palm.system.vitality.emission_window import sample_emission_window
from palm.system.vitality.loaded_bulk import sample_loaded_bulk
from palm.system.vitality.process_resources import sample_process_resources
from palm.system.vitality.report import SeatReport, reports_to_dicts
from palm.system.vitality.schema import (
    CAPABILITY_BENCHMARK,
    CAPABILITY_EMISSION_WINDOW,
    CAPABILITY_LOADED_BULK,
    CAPABILITY_MONITOR_AGENT,
    CAPABILITY_PROCESS_RESOURCES,
    CAPABILITY_SEAT_WALK,
    COST_CHEAP,
    COST_MODERATE,
    LINEAGE_NATIVE,
    LINEAGE_SAMPLED,
    MATURITY_INSTALLED,
    ROLE_OBSERVE,
    ROLE_TOOL,
    STATE_ABSENT,
    STATE_ERROR,
    STATE_OK,
)
from palm.system.vitality.walk import WalkOptions, walk_result

BAG_SEAT_REPORTS = "seat_reports"
BAG_SEAT_WALK_RESULT = "seat_walk_result"


def _summarize_seats(reports: list[SeatReport]) -> dict[str, Any]:
    """Aggregate only structural fields — no load interpretation."""
    by_state: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    by_lineage: dict[str, int] = {}
    present = 0
    for r in reports:
        by_state[r.state] = by_state.get(r.state, 0) + 1
        by_kind[r.kind] = by_kind.get(r.kind, 0) + 1
        by_lineage[r.lineage] = by_lineage.get(r.lineage, 0) + 1
        if r.present:
            present += 1
    return {
        "seat_count": len(reports),
        "present_count": present,
        "absent_count": by_state.get(STATE_ABSENT, 0),
        "error_count": by_state.get(STATE_ERROR, 0),
        "ok_count": by_state.get(STATE_OK, 0),
        "by_state": by_state,
        "by_kind": by_kind,
        "by_lineage": by_lineage,
        "native_count": by_lineage.get(LINEAGE_NATIVE, 0),
        "sampled_count": by_lineage.get(LINEAGE_SAMPLED, 0),
        "present_ids": [r.seat_id for r in reports if r.present],
        "absent_ids": [r.seat_id for r in reports if r.state == STATE_ABSENT],
    }


def sample_seat_walk(instance: Any, ctx: SampleContext) -> CapabilityFragment:
    """Core capability: discover seats on the live instance."""
    # Reuse reports if projection or a prior cap already walked.
    cached = ctx.bag.get(BAG_SEAT_REPORTS)
    if isinstance(cached, list) and cached and isinstance(cached[0], SeatReport):
        reports = list(cached)
        summary = _summarize_seats(reports)
    else:
        options = ctx.walk_options
        if options is not None and not isinstance(options, WalkOptions):
            options = None
        result = walk_result(instance, options)
        reports = list(result.reports)
        ctx.bag[BAG_SEAT_REPORTS] = reports
        ctx.bag[BAG_SEAT_WALK_RESULT] = result
        summary = _summarize_seats(reports)
        summary["probe_count"] = result.probe_count

    return CapabilityFragment.ok(
        CAPABILITY_SEAT_WALK,
        {
            "seats": reports_to_dicts(reports),
            "summary": summary,
        },
        notes=[],
        meta={"capability": CAPABILITY_SEAT_WALK},
    )


def build_seat_walk_capability() -> VitalityCapability:
    return VitalityCapability(
        id=CAPABILITY_SEAT_WALK,
        sample=sample_seat_walk,
        role=ROLE_OBSERVE,
        maturity=MATURITY_INSTALLED,
        default_enabled=True,
        cost=COST_CHEAP,
        description="Discover living seats; fold seat reports (no second write path)",
        tags=("core", "observe"),
        order=10,
    )


def build_emission_window_capability() -> VitalityCapability:
    return VitalityCapability(
        id=CAPABILITY_EMISSION_WINDOW,
        sample=sample_emission_window,
        role=ROLE_OBSERVE,
        maturity=MATURITY_INSTALLED,
        default_enabled=True,
        cost=COST_CHEAP,
        description=(
            "Recent system-log emissions + actor_kind partition; "
            "optional work_plane heat (no second write path)"
        ),
        tags=("core", "observe", "emission"),
        order=20,
    )


def build_process_resources_capability() -> VitalityCapability:
    return VitalityCapability(
        id=CAPABILITY_PROCESS_RESOURCES,
        sample=sample_process_resources,
        role=ROLE_OBSERVE,
        maturity=MATURITY_INSTALLED,
        default_enabled=True,
        cost=COST_CHEAP,
        description=(
            "Host-process RSS/CPU/threads (stdlib resource + optional /proc); "
            "units labeled; not a health grade"
        ),
        tags=("observe", "load", "process"),
        order=50,
    )


def build_loaded_bulk_capability() -> VitalityCapability:
    return VitalityCapability(
        id=CAPABILITY_LOADED_BULK,
        sample=sample_loaded_bulk,
        role=ROLE_OBSERVE,
        maturity=MATURITY_INSTALLED,
        default_enabled=True,
        cost=COST_CHEAP,
        description=(
            "Light bulk of attached seats / loaded modules "
            "(LOC · public callables · composition counts); visibility not shame"
        ),
        tags=("observe", "bulk", "structure"),
        order=60,
    )


def build_default_capabilities() -> list[VitalityCapability]:
    """Installed observe + intention stubs for catalog honesty."""
    return [
        build_seat_walk_capability(),
        build_emission_window_capability(),
        build_process_resources_capability(),
        build_loaded_bulk_capability(),
        build_benchmark_capability(),
        intention_stub(
            CAPABILITY_MONITOR_AGENT,
            role=ROLE_TOOL,
            description="Monitor agent tool (grow when ready)",
            order=110,
            tags=("tool", "intention"),
        ),
    ]


def build_benchmark_capability() -> VitalityCapability:
    """Active tool — off by default so everyday project() does not thrash."""
    return VitalityCapability(
        id=CAPABILITY_BENCHMARK,
        sample=sample_benchmark,
        role=ROLE_TOOL,
        maturity=MATURITY_INSTALLED,
        default_enabled=False,
        cost=COST_MODERATE,
        description=(
            "Controlled load recipe between two observe projections; "
            "diff RSS/CPU · seats · emissions · bulk (run via run_benchmark "
            "or extra_enable; not on by default)"
        ),
        tags=("tool", "benchmark", "load"),
        order=100,
    )


__all__ = [
    "BAG_SEAT_REPORTS",
    "BAG_SEAT_WALK_RESULT",
    "build_benchmark_capability",
    "build_default_capabilities",
    "build_emission_window_capability",
    "build_loaded_bulk_capability",
    "build_process_resources_capability",
    "build_seat_walk_capability",
    "sample_benchmark",
    "sample_emission_window",
    "sample_loaded_bulk",
    "sample_process_resources",
    "sample_seat_walk",
]
