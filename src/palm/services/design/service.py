"""Design service — propose, validate, impact, and commit flow revisions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from palm.common.exceptions import DesignProposalNotFoundError
from palm.common.services.base import BaseService
from palm.common.services.errors import (
    DefinitionNotFoundServiceError,
    DesignProposalNotFoundServiceError,
)
from palm.common.services.errors import DesignCommitRejectedServiceError
from palm.services.design.proposal import DesignProposalRepository, resolve_flow_id_from_body
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
        proposals: DesignProposalRepository,
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
        try:
            catalog_validation = self._definitions.validate_flow(
                _validation_body(proposal.body),
                runtime=runtime,
            )
        except (TypeError, ValueError, KeyError) as exc:
            catalog_validation = {"valid": False, "error": str(exc)}

        ok, blockers = run_design_validators(proposal.body, context=self)
        valid = bool(catalog_validation.get("valid", False)) and ok
        result = {
            "proposal_id": proposal.proposal_id,
            "valid": valid,
            "dry_run": dry_run,
            "catalog": catalog_validation,
            "blockers": blockers,
        }
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
        return impact

    def commit_proposal(self, proposal_id: str) -> dict[str, Any]:
        proposal = self._proposals.get(proposal_id)
        if proposal.status != "open":
            raise DesignCommitRejectedServiceError(
                proposal_id,
                f"proposal status is {proposal.status!r}, expected 'open'",
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

        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "flow_id": proposal.flow_id,
            "revision": proposal.committed_revision,
            "flow": published,
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