"""WaitPlaneService — first-class **continue** plane (0.55.10).

Peer of work-drain (**start**): completer events on the event engine match
open wait interests and resume or fail owner jobs. Install wires
collaborators; the plane never holds a full runtime.
Completers never import this plane (register-downward).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.system.subsystems.planes.wait.deliver import deliver_wait_completion
from palm.system.subsystems.planes.wait.index import WaitOwnerIndex
from palm.system.subsystems.planes.wait.matcher import MatchDisposition, WaitMatcher
from palm.system.subsystems.planes.wait.present import summarize_waiting_on, waiting_on_from_job
from palm.system.subsystems.planes.wait.signals import TargetSignal
from palm.core.orchestration.job import JobStatus
from palm.core.orchestration.run_result import RunResult
from palm.core.wait import (
    WaitInterest,
    close_wait_on_job,
    list_waits_on_job,
    open_wait_on_job,
    rehydrate_wait_interests,
)

if TYPE_CHECKING:
    from palm.core.event import EventEngine


class WaitPlaneService:
    """Continue plane: interest open/close + event match → resume/fail.

    Lifecycle:
    * :meth:`attach` — wire orchestration + optional event engine + *able*
    * :meth:`detach` — unsubscribe

    **0.63.26:** *able* gates **resume** (product continue). Default fail closed.
    Target **fail** still applies (honest completer failure). Install wires the
    ready query (``started ∧ may_run_business``). Work-plane able may also
    require ``work_drain`` (0.67.2) — continue does not.
    """

    def __init__(self) -> None:
        self._index = WaitOwnerIndex()
        self._matcher: WaitMatcher | None = None
        self._orchestration: Any | None = None
        # 0.63.26 — fail closed until install wires admission/started able.
        self._able: Callable[[], bool] = lambda: False
        self._refused_resumes = 0

    @property
    def matcher(self) -> WaitMatcher | None:
        return self._matcher

    @property
    def index(self) -> WaitOwnerIndex:
        return self._index

    @property
    def is_attached(self) -> bool:
        return self._matcher is not None and bool(getattr(self._matcher, "_subs", None))

    def set_able(self, able: Callable[[], bool] | None) -> None:
        """Replace able probe; *None* restores fail-closed default."""
        self._able = able if able is not None else (lambda: False)

    def is_able(self) -> bool:
        try:
            return bool(self._able())
        except Exception:
            return False

    def attach(
        self,
        *,
        orchestration: Any,
        event: EventEngine | None = None,
        able: Callable[[], bool] | None = None,
    ) -> WaitMatcher:
        """Wire matcher to orchestration job store and optional event bus.

        Callers extract collaborators — the plane does not take or store a
        full runtime.

        *able* — when false, match→resume fails the owner closed (admission law);
        omit / *None* fails closed (0.63.26).
        """
        if self._matcher is not None:
            self.detach()
        orch = orchestration
        self._orchestration = orch
        self._able = able if able is not None else (lambda: False)
        self._refused_resumes = 0

        def get_job(job_id: str) -> Any:
            try:
                return orch.get_job(job_id)
            except Exception:
                return None

        def list_jobs() -> list[Any]:
            return list(orch.jobs.values())

        def resume_owner(
            owner_id: str,
            interest: WaitInterest,
            _signal: TargetSignal,
        ) -> None:
            job = get_job(owner_id)
            if job is None:
                return
            if not self.is_able():
                # 0.63.26 — product continue: do not re-drive business when
                # admission/started is down. Fail closed (not soft resume dig).
                self._refused_resumes += 1
                from palm.system.structure.errors import AdmissionRefusedError

                if not job.is_terminal:
                    orch.apply_result(
                        job,
                        RunResult(
                            status=JobStatus.FAILED,
                            error=AdmissionRefusedError(None),
                        ),
                    )
                close_wait_on_job(job, kind=interest.kind, target_id=interest.target_id)
                self._index.unregister(
                    owner_id, kind=interest.kind, target_id=interest.target_id
                )
                return
            # Kind/source-pluggable delivery (0.55.16); nested is default register.
            deliver_wait_completion(job, interest, get_job)
            close_wait_on_job(job, kind=interest.kind, target_id=interest.target_id)
            self._index.unregister(
                owner_id, kind=interest.kind, target_id=interest.target_id
            )
            if job.status != JobStatus.WAITING_FOR_INPUT:
                return
            orch.resume_job(owner_id)

        def fail_owner(
            owner_id: str,
            _interest: WaitInterest,
            signal: TargetSignal,
        ) -> None:
            job = get_job(owner_id)
            if job is None or job.is_terminal:
                return
            msg = (
                f"Wait target {signal.kind}:{signal.target_id} ended with "
                f"{signal.outcome}"
            )
            orch.apply_result(
                job,
                RunResult(status=JobStatus.FAILED, error=RuntimeError(msg)),
            )

        matcher = WaitMatcher(
            index=self._index,
            get_job=get_job,
            list_jobs=list_jobs,
            resume_owner=resume_owner,
            fail_owner=fail_owner,
        )
        if event is not None:
            matcher.attach_events(event)
        self._matcher = matcher
        # 0.55.11 — index is load-bearing; rebuild from live job state.
        self.rebuild_index()
        return matcher

    def detach(self) -> None:
        if self._matcher is not None:
            self._matcher.detach_events()
            self._matcher = None
        self._index.clear()
        self._orchestration = None
        self._able = lambda: False

    def rebuild_index(self) -> int:
        """Rebuild target→owners index from live jobs' open interests. Returns count."""
        self._index.clear()
        orch = self._orchestration
        if orch is None:
            return 0
        n = 0
        for job in list(orch.jobs.values()):
            try:
                waits = list_waits_on_job(job)
            except Exception:
                continue
            for w in waits:
                self._index.register(str(job.id), w)
                n += 1
        return n

    def open_on_job(
        self,
        job: Any,
        interest: WaitInterest,
        **kwargs: Any,
    ) -> WaitInterest:
        """Open interest on job state and register owner index (sole open path)."""
        opened = open_wait_on_job(job, interest, **kwargs)
        self._index.register(str(job.id), opened)
        return opened

    def close_on_job(
        self,
        job: Any,
        *,
        kind: str,
        target_id: str,
    ) -> WaitInterest | None:
        """Close interest on job state and drop index entry."""
        closed = close_wait_on_job(job, kind=kind, target_id=target_id)
        self._index.unregister(str(job.id), kind=kind, target_id=target_id)
        return closed

    def rehydrate_state(self, state: Any) -> list[WaitInterest]:
        """Normalize wait interests after snapshot restore."""
        return rehydrate_wait_interests(state)

    def rehydrate_job(self, job: Any) -> list[WaitInterest]:
        """Normalize interests on ``job.state`` and refresh index for that owner."""
        interests = rehydrate_wait_interests(job.state)
        owner_id = str(job.id)
        self._index.unregister_all_for_owner(owner_id)
        for w in interests:
            self._index.register(owner_id, w)
        return interests

    def handle_payload(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        event_id: str | None = None,
    ) -> list[MatchDisposition]:
        if self._matcher is None:
            return []
        return self._matcher.handle_payload(event_type, payload, event_id=event_id)

    def doctor_snapshot(self, jobs: list[Any] | None = None) -> dict[str, Any]:
        """Compact continue-plane health for doctor / control plane."""
        job_list = jobs
        if job_list is None and self._orchestration is not None:
            job_list = list(self._orchestration.jobs.values())
        job_list = job_list or []
        open_owners = 0
        open_interests = 0
        wait_kinds: dict[str, int] = {}
        for job in job_list:
            rows = waiting_on_from_job(job)
            if not rows:
                continue
            open_owners += 1
            open_interests += len(rows)
            for row in rows:
                kind = str(row.get("kind") or "unknown")
                wait_kinds[kind] = wait_kinds.get(kind, 0) + 1
        return {
            "wait_plane_attached": self._matcher is not None,
            "wait_matcher_wired": self._matcher is not None,
            "open_wait_owners": open_owners,
            "open_wait_interests": open_interests,
            "wait_kinds": wait_kinds,
            "able": self.is_able(),
            "refused_resumes": self._refused_resumes,
            "verbs": ["start", "continue"],
            "index_size": len(self._index),
            "note": (
                "start = trigger → WorkIntent; continue = WaitPlaneService "
                "(VISION-0.55.10 / 0.55.16 deliver registry); "
                "resume gated by able / admission (0.63.26)"
            ),
        }

    def waiting_on_for_job(self, job: Any) -> list[dict[str, Any]]:
        return waiting_on_from_job(job)

    def waiting_on_summary_for_job(self, job: Any) -> dict[str, Any] | None:
        rows = waiting_on_from_job(job)
        return summarize_waiting_on(rows)


__all__ = ["WaitPlaneService"]
