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
from palm.services.definitions.parsers import parse_resource
from palm.services.design.envelope import (
    PublishAction,
    extract_resource_dict,
    resolve_flow_id_from_body,
    resolve_publish_intent,
    resolve_resource_id_from_body,
    resolve_resource_publish_intent,
    validation_body,
)
from palm.services.design.impact_scan import flows_referencing_resource
from palm.services.design.proposal import (
    ProposalRepository,
    resolve_proposal_flow_id,
    resolve_proposal_resource_id,
)
from palm.services.design.dispatch import dispatch_design_command
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
        proposals: ProposalRepository,
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
        return dispatch_design_command(self, path, params)

    def propose_flow(
        self,
        body: dict[str, Any],
        *,
        base_flow_id: str | None = None,
    ) -> dict[str, Any]:
        """Store a flow proposal and return a validation preview."""
        flow_id = resolve_flow_id_from_body(body, base_flow_id=base_flow_id)
        proposal = self._proposals.create(
            body,
            kind="flow",
            base_flow_id=base_flow_id,
            flow_id=flow_id,
        )
        validation = self.validate_proposal(proposal.proposal_id, dry_run=True)
        proposal.validation = validation
        self._proposals.save(proposal)
        return {
            "proposal": proposal.to_dict(),
            "validation": validation,
        }

    def propose_resource(
        self,
        body: dict[str, Any],
        *,
        base_resource_id: str | None = None,
    ) -> dict[str, Any]:
        """Store a resource proposal and return a validation preview."""
        resource_id = resolve_resource_id_from_body(body, base_resource_id=base_resource_id)
        proposal = self._proposals.create(
            body,
            kind="resource",
            base_resource_id=base_resource_id,
            resource_id=resource_id,
        )
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
        ok, blockers = run_design_validators(proposal.body, context=self)
        if proposal.kind == "resource":
            catalog_validation = self._validate_resource_catalog(proposal.body)
        else:
            runtime = self._resolve_runtime()
            try:
                catalog_validation = self._definitions.validate_flow(
                    validation_body(proposal.body),
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
        if proposal.kind == "resource":
            return self._analyze_resource_proposal_impact(proposal)
        flow_id = resolve_proposal_flow_id(proposal)
        if not flow_id:
            raise DesignCommitRejectedServiceError(
                proposal_id,
                "proposal has no resolvable flow_id for impact analysis",
            )
        target_revision = self._definitions.next_revision_for_flow(flow_id)
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

        if proposal.kind == "resource":
            return self._commit_resource_proposal(proposal_id, proposal)

        intent = resolve_publish_intent(
            body=proposal.body,
            base_flow_id=proposal.base_flow_id,
            flow_id=proposal.flow_id,
            flow_exists=self._flow_exists,
        )
        if intent is None:
            raise DesignCommitRejectedServiceError(proposal_id, "cannot resolve flow_id to publish")

        impact = self.analyze_proposal_impact(proposal_id)

        if intent.action == PublishAction.UPDATE:
            published = self._definitions.update_flow(intent.flow_id, proposal.body)
        else:
            published = self._definitions.create_flow(proposal.body)

        proposal.status = "committed"
        proposal.committed_revision = int(published.get("revision") or 1)
        proposal.flow_id = str(published.get("definition_id") or published.get("name") or intent.flow_id)
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

    def publish_flow(
        self,
        body: dict[str, Any],
        *,
        base_flow_id: str | None = None,
    ) -> dict[str, Any]:
        """One-shot propose → impact → commit for weak-LLM agents (0.30.4).

        Stops without commit when validation fails. Impact is always run when
        valid so agents get a single response with ``status`` and next ``actions``.
        """
        proposed = self.propose_flow(body, base_flow_id=base_flow_id)
        proposal = proposed.get("proposal") or {}
        proposal_id = str(proposal.get("proposal_id") or "")
        validation = proposed.get("validation") or {}
        if not validation.get("valid"):
            return {
                "status": "blocked",
                "stage": "validate",
                "proposal_id": proposal_id,
                "proposal": proposal,
                "validation": validation,
                "hint": (
                    "Fix validation blockers and call palm_design_publish_flow again, "
                    "or palm_design_propose_flow for a step-by-step loop."
                ),
                "actions": [
                    {
                        "label": "Retry publish",
                        "tool": "palm_design_publish_flow",
                    },
                    {
                        "label": "Discard proposal",
                        "tool": "palm_design_discard",
                        "params": {"proposal_id": proposal_id},
                    },
                ],
            }

        impact = self.analyze_proposal_impact(proposal_id)
        mutation = impact.get("mutation") if isinstance(impact, dict) else None
        commit_token = None
        if isinstance(mutation, dict):
            commit_token = mutation.get("commit_token") or mutation.get("input_token")

        committed = self.commit_proposal(
            proposal_id,
            commit_token=str(commit_token) if commit_token else None,
        )
        flow_id = committed.get("flow_id")
        return {
            "status": "committed",
            "stage": "commit",
            "proposal_id": proposal_id,
            "flow_id": flow_id,
            "revision": committed.get("revision"),
            "migrations": committed.get("migrations"),
            "impact_summary": (impact.get("summary") if isinstance(impact, dict) else None),
            "hint": (
                f"Published {flow_id!r}. Run with palm_flows_create_session "
                f"or palm_assist(path=['flows', {flow_id!r}, 'create'])."
            ),
            "actions": [
                {
                    "label": "Run published flow",
                    "tool": "palm_flows_create_session",
                    "params": {"flow_id": flow_id},
                },
                {
                    "label": "Describe flow",
                    "tool": "palm_flows_describe",
                    "params": {"flow_id": flow_id},
                },
            ],
            "flow": committed.get("flow"),
        }

    def publish_resource(
        self,
        body: dict[str, Any],
        *,
        base_resource_id: str | None = None,
    ) -> dict[str, Any]:
        """One-shot propose → impact → commit for resource definitions (0.30.4)."""
        proposed = self.propose_resource(body, base_resource_id=base_resource_id)
        proposal = proposed.get("proposal") or {}
        proposal_id = str(proposal.get("proposal_id") or "")
        validation = proposed.get("validation") or {}
        if not validation.get("valid"):
            return {
                "status": "blocked",
                "stage": "validate",
                "proposal_id": proposal_id,
                "proposal": proposal,
                "validation": validation,
                "hint": "Fix validation blockers, then call palm_design_publish_resource again.",
                "actions": [
                    {
                        "label": "Discard proposal",
                        "tool": "palm_design_discard",
                        "params": {"proposal_id": proposal_id},
                    },
                ],
            }

        impact = self.analyze_proposal_impact(proposal_id)
        mutation = impact.get("mutation") if isinstance(impact, dict) else None
        commit_token = None
        if isinstance(mutation, dict):
            commit_token = mutation.get("commit_token") or mutation.get("input_token")

        committed = self.commit_proposal(
            proposal_id,
            commit_token=str(commit_token) if commit_token else None,
        )
        resource_ref = committed.get("resource_ref") or committed.get("resource_id")
        return {
            "status": "committed",
            "stage": "commit",
            "proposal_id": proposal_id,
            "resource_ref": resource_ref,
            "impact_summary": (impact.get("summary") if isinstance(impact, dict) else None),
            "hint": "Resource published. Reference it from flow steps via resource_ref.",
            "result": committed,
        }

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

    def _resource_exists(self, resource_ref: str) -> bool:
        try:
            self._definitions.get_resource(resource_ref)
            return True
        except DefinitionNotFoundServiceError:
            return False

    def _validate_resource_catalog(self, body: dict[str, Any]) -> dict[str, Any]:
        payload = extract_resource_dict(body) or body
        try:
            resource = parse_resource(payload)
        except (TypeError, ValueError, KeyError) as exc:
            return {"valid": False, "kind": "resource", "error": str(exc)}
        return {
            "valid": True,
            "kind": "resource",
            "resource": resource.name,
            "provider": resource.provider,
        }

    def _analyze_resource_proposal_impact(self, proposal: Any) -> dict[str, Any]:
        resource_ref = resolve_proposal_resource_id(proposal)
        if not resource_ref:
            raise DesignCommitRejectedServiceError(
                proposal.proposal_id,
                "proposal has no resolvable resource_id for impact analysis",
            )
        references = flows_referencing_resource(
            self._definitions.list_flow_definitions(),
            resource_ref,
        )
        impact = {
            "kind": "resource",
            "resource_ref": resource_ref,
            "referencing_flows": references,
            "summary": {
                "total_references": len(references),
                "new_resource": not self._resource_exists(resource_ref),
            },
        }
        proposal.impact = impact
        self._proposals.save(proposal)
        valid = bool((proposal.validation or {}).get("valid"))
        mutation = build_commit_mutation_block(proposal.proposal_id, valid=valid)
        if mutation is not None:
            impact = dict(impact)
            impact["mutation"] = mutation
        return impact

    def _commit_resource_proposal(self, proposal_id: str, proposal: Any) -> dict[str, Any]:
        intent = resolve_resource_publish_intent(
            body=proposal.body,
            base_resource_id=proposal.base_resource_id,
            resource_id=proposal.resource_id,
            resource_exists=self._resource_exists,
        )
        if intent is None:
            raise DesignCommitRejectedServiceError(proposal_id, "cannot resolve resource_id to publish")

        impact = self.analyze_proposal_impact(proposal_id)
        payload = extract_resource_dict(proposal.body) or proposal.body

        if intent.action == PublishAction.UPDATE:
            published = self._definitions.update_resource(intent.flow_id, payload)
        else:
            published = self._definitions.create_resource(payload)

        proposal.status = "committed"
        proposal.resource_id = str(
            published.get("name") or published.get("definition_id") or intent.flow_id
        )
        self._proposals.save(proposal)

        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "kind": "resource",
            "resource_ref": proposal.resource_id,
            "resource": published,
            "impact": impact,
        }


__all__ = ["DesignService"]