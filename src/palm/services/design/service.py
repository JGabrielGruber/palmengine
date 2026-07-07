"""Design service — propose, validate, impact, and commit flow revisions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.exceptions import DefinitionBuildError, DesignProposalNotFoundError
from palm.common.services.base import BaseService
from palm.common.services.errors import (
    DefinitionNotFoundServiceError,
    DesignCommitRejectedServiceError,
    DesignProposalNotFoundServiceError,
    InstanceMigrationServiceError,
)
from palm.services.design.commit_gate import build_commit_mutation_block, enforce_commit_token
from palm.services.design.proposal import resolve_flow_id_from_body
from palm.services.design.registry import run_design_validators

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime
    from palm.services.definitions.service import DefinitionService


class DesignService(BaseService):
    """Structured definition evolution atop revisioned catalog."""

    def __init__(
        self,
        *,
        commands: Any,
        queries: Any,
        schemas: Any,
        definitions: DefinitionService,
        proposals: Any,
        runtime: BaseRuntime | None = None,
        runtime_resolver: Callable[[str | None], BaseRuntime] | None = None,
    ) -> None:
        super().__init__(commands=commands, queries=queries, schemas=schemas)
        self._definitions = definitions
        self._proposals = proposals
        self._runtime = runtime
        self._runtime_resolver = runtime_resolver

    @property
    def definitions(self) -> DefinitionService:
        return self._definitions

    def dispatch(
        self,
        path: list[str] | tuple[str, ...],
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a design command path."""
        params = params or {}
        segments = [str(item) for item in path]
        if segments == ["design", "propose"]:
            body = dict(params.get("body") or params)
            base_flow_id = params.get("base_flow_id")
            payload = {
                key: value
                for key, value in body.items()
                if key not in {"base_flow_id", "body", "commit_token", "input_token"}
            }
            return self.propose_flow(payload, base_flow_id=base_flow_id)
        if segments == ["design", "proposals"]:
            return {"proposals": self.list_proposals(flow_id=params.get("flow_id"))}
        if len(segments) == 3 and segments[:2] == ["design", "proposals"]:
            return self.get_proposal(segments[2])
        if len(segments) == 4 and segments[:2] == ["design", "proposals"] and segments[3] == "validate":
            return self.validate_proposal(segments[2], dry_run=True)
        if len(segments) == 4 and segments[:2] == ["design", "proposals"] and segments[3] == "impact":
            return self.analyze_proposal_impact(segments[2])
        if len(segments) == 4 and segments[:2] == ["design", "proposals"] and segments[3] == "commit":
            return self.commit_proposal(
                segments[2],
                commit_token=params.get("commit_token"),
                input_token=params.get("input_token"),
            )
        if len(segments) == 4 and segments[:2] == ["design", "proposals"] and segments[3] == "discard":
            return self.discard_proposal(segments[2])
        raise ValueError(f"unrecognized design dispatch path: {'/'.join(segments)}")

    def propose_flow(
        self,
        body: dict[str, Any],
        *,
        base_flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Store a proposal and return a validation preview."""
        flow_id = resolve_flow_id_from_body(body, base_flow_id=base_flow_id)
        proposal = self._proposals.create(body, base_flow_id=base_flow_id, flow_id=flow_id)
        validation = self.validate_proposal(proposal.proposal_id, dry_run=True)
        proposal.validation = validation
        self._proposals.save(proposal)
        return {
            "proposal": proposal.to_dict(),
            "validation": validation,
        }

    def get_proposal(self, proposal_id: str) -> dict[str, Any]:
        try:
            return self._proposals.get(proposal_id).to_dict()
        except DesignProposalNotFoundError as exc:
            raise DesignProposalNotFoundServiceError(proposal_id) from exc

    def list_proposals(self, *, flow_id: str | None = None) -> list[dict[str, Any]]:
        rows = self._proposals.list_proposals(flow_id=flow_id, status="open")
        return [row.to_dict() for row in rows]

    def validate_proposal(self, proposal_id: str, *, dry_run: bool = True) -> dict[str, Any]:
        proposal = self._proposals.get(proposal_id)
        runtime = self._resolve_runtime()
        ok, blockers = run_design_validators(proposal.body, context=self)
        try:
            catalog_validation = self._definitions.validate_flow(
                _validation_body(proposal.body),
                runtime=runtime,
            )
        except (TypeError, ValueError, KeyError, DefinitionBuildError) as exc:
            catalog_validation = {"valid": False, "error": str(exc)}

        valid = bool(catalog_validation.get("valid", False)) and ok
        result: dict[str, Any] = {
            "proposal_id": proposal.proposal_id,
            "valid": valid,
            "dry_run": dry_run,
            "catalog": catalog_validation,
            "blockers": blockers,
        }
        mutation = build_commit_mutation_block(proposal_id, valid=valid)
        if mutation is not None:
            result["mutation"] = mutation
        proposal.validation = result
        self._proposals.save(proposal)
        return result

    def analyze_proposal_impact(self, proposal_id: str) -> dict[str, Any]:
        proposal = self._proposals.get(proposal_id)
        flow_id = proposal.flow_id or resolve_flow_id_from_body(
            proposal.body,
            base_flow_id=proposal.base_flow_id,
        )
        if not flow_id:
            raise DesignCommitRejectedServiceError(
                proposal_id,
                "proposal has no resolvable flow_id for impact analysis",
            )
        target_revision = self._target_revision_for_proposal(flow_id)
        try:
            impact = self._definitions.analyze_impact(flow_id, target_revision=target_revision)
        except DefinitionNotFoundServiceError as exc:
            if proposal.base_flow_id is None:
                impact = {
                    "flow_id": flow_id,
                    "latest_revision": 0,
                    "target_revision": 1,
                    "instances": [],
                    "summary": {
                        "total": 0,
                        "behind_latest": 0,
                        "compatible": 0,
                        "snapshot_only": 0,
                        "blocked": 0,
                        "new_flow": True,
                    },
                }
            else:
                raise exc
        proposal.impact = impact
        self._proposals.save(proposal)
        valid = bool((proposal.validation or {}).get("valid"))
        mutation = build_commit_mutation_block(proposal_id, valid=valid)
        if mutation is not None:
            impact = dict(impact)
            impact["mutation"] = mutation
        return impact

    def commit_proposal(
        self,
        proposal_id: str,
        *,
        commit_token: str | None = None,
        input_token: str | None = None,
    ) -> dict[str, Any]:
        proposal = self._proposals.get(proposal_id)
        if proposal.status != "open":
            raise DesignCommitRejectedServiceError(
                proposal_id,
                f"proposal status is {proposal.status!r}, expected 'open'",
            )

        enforce_commit_token(
            proposal_id,
            commit_token=commit_token,
            input_token=input_token,
        )

        validation = self.validate_proposal(proposal_id, dry_run=False)
        if not validation.get("valid"):
            blockers = list(validation.get("blockers") or [])
            if not validation.get("catalog", {}).get("valid", False):
                blockers.append("catalog validation failed")
            raise DesignCommitRejectedServiceError(
                proposal_id,
                "validation failed",
                blockers=blockers,
            )

        flow_id = proposal.flow_id or resolve_flow_id_from_body(
            proposal.body,
            base_flow_id=proposal.base_flow_id,
        )
        if not flow_id:
            raise DesignCommitRejectedServiceError(proposal_id, "cannot resolve flow_id to publish")

        impact = proposal.impact or self.analyze_proposal_impact(proposal_id)

        try:
            if proposal.base_flow_id or self._flow_exists(flow_id):
                published = self._definitions.update_flow(flow_id, proposal.body)
            else:
                published = self._definitions.create_flow(proposal.body)
        except DefinitionNotFoundServiceError:
            published = self._definitions.create_flow(proposal.body)

        proposal.status = "committed"
        proposal.committed_revision = int(published.get("revision") or 1)
        proposal.flow_id = str(published.get("definition_id") or published.get("name") or flow_id)
        self._proposals.save(proposal)

        migrations = self._auto_migrate_compatible_instances(
            proposal.flow_id,
            proposal.committed_revision,
            impact,
        )

        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "flow_id": proposal.flow_id,
            "revision": proposal.committed_revision,
            "flow": published,
            "migrations": migrations,
        }

    def discard_proposal(self, proposal_id: str) -> dict[str, Any]:
        try:
            proposal = self._proposals.get(proposal_id)
        except DesignProposalNotFoundError as exc:
            raise DesignProposalNotFoundServiceError(proposal_id) from exc
        proposal.status = "discarded"
        self._proposals.save(proposal)
        self._proposals.delete(proposal_id)
        return {"proposal_id": proposal_id, "discarded": True}

    def _auto_migrate_compatible_instances(
        self,
        flow_id: str,
        target_revision: int,
        impact: dict[str, Any],
    ) -> dict[str, Any]:
        summary = {
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped_blocked": 0,
            "skipped_other": 0,
            "results": [],
        }
        for row in impact.get("instances") or []:
            if not isinstance(row, dict):
                continue
            instance_id = str(row.get("instance_id") or "")
            if not instance_id:
                continue
            compatibility = str(row.get("compatibility") or "")
            if compatibility == "blocked":
                summary["skipped_blocked"] += 1
                summary["results"].append(
                    {
                        "instance_id": instance_id,
                        "status": "skipped",
                        "detail": "blocked",
                        "blockers": list(row.get("blockers") or []),
                    }
                )
                continue
            if not row.get("compatible"):
                summary["skipped_other"] += 1
                summary["results"].append(
                    {
                        "instance_id": instance_id,
                        "status": "skipped",
                        "detail": compatibility or "not_compatible",
                    }
                )
                continue

            summary["attempted"] += 1
            try:
                self._definitions.migrate_instance(
                    instance_id,
                    target_revision=target_revision,
                    dry_run=False,
                )
            except InstanceMigrationServiceError as exc:
                summary["failed"] += 1
                summary["results"].append(
                    {
                        "instance_id": instance_id,
                        "status": "failed",
                        "detail": exc.reason,
                        "blockers": list(exc.blockers or []),
                    }
                )
                continue
            except Exception as exc:
                summary["failed"] += 1
                summary["results"].append(
                    {
                        "instance_id": instance_id,
                        "status": "failed",
                        "detail": str(exc),
                    }
                )
                continue

            summary["succeeded"] += 1
            summary["results"].append({"instance_id": instance_id, "status": "ok"})
        summary["flow_id"] = flow_id
        summary["target_revision"] = target_revision
        return summary

    def _resolve_runtime(self) -> BaseRuntime:
        if self._runtime is not None:
            return self._runtime
        if self._runtime_resolver is not None:
            return self._runtime_resolver(None)
        raise RuntimeError("DesignService requires runtime or runtime_resolver for validation")

    def _flow_exists(self, flow_id: str) -> bool:
        try:
            self._definitions.get_flow(flow_id, verbose=False)
            return True
        except DefinitionNotFoundServiceError:
            return False

    def _target_revision_for_proposal(self, flow_id: str) -> int:
        latest = self._definitions._repository.get_latest_revision(flow_id)
        if latest is None:
            try:
                flow = self._definitions._repository.get_flow(flow_id)
                return int(flow.revision or 1) + 1
            except Exception:
                return 1
        return latest + 1


def _validation_body(body: dict[str, Any]) -> dict[str, Any]:
    """Normalize proposal payload for ``validate_flow`` (expects ``flow`` wrapper)."""
    if "flow" in body or "wizard" in body or "flow_name" in body:
        return body
    return {"flow": body}


__all__ = ["DesignService"]