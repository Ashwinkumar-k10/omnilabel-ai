"""Human review, disposition workspace, and explicit approval gating engine."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from src.schemas import (
    ImpactInventory,
    RuleResult,
    FindingCategory,
    ReviewDecision,
    ReleaseState,
    ScopeDisposition
)


class ReviewWorkflowEngine:
    """
    Enforces quality and regulatory gating conditions:
    1. Scope Gate: All orphan candidates must have explicit human disposition.
    2. Verification Gate: No unresolved critical rule failures.
    3. Authorization Gate: Explicit qualified human sign-off.
    """

    @staticmethod
    def evaluate_release_readiness(
        inventory: ImpactInventory,
        rule_results: List[RuleResult]
    ) -> Tuple[ReleaseState, List[str]]:
        """
        Determines current release state and returns blocking reasons.
        """
        blocking_reasons: List[str] = []

        # Gate 1: Check Scope Completeness
        unresolved_orphans = [
            o.variant_id for o in inventory.orphan_candidates
            if o.disposition == ScopeDisposition.UNRESOLVED
        ]
        if unresolved_orphans:
            blocking_reasons.append(
                f"Scope incomplete: {len(unresolved_orphans)} orphan candidate(s) "
                f"remain unresolved in Uncertainty Queue: {', '.join(unresolved_orphans)}."
            )
            return ReleaseState.SCOPE_BLOCKED, blocking_reasons

        # Gate 2: Check Deterministic Rule Failures
        critical_failures = [
            r for r in rule_results
            if r.category == FindingCategory.CRITICAL_RULE_FAILURE and r.status == "FAIL"
        ]
        if critical_failures:
            reasons = [f"[{r.rule_id}] {r.message}" for r in critical_failures]
            blocking_reasons.extend(reasons)
            return ReleaseState.CHECKS_FAILED, blocking_reasons

        # Ready for explicit human sign-off
        return ReleaseState.PENDING_HUMAN_APPROVAL, []

    @staticmethod
    def record_decision(
        eco_id: str,
        variant_id: str,
        reviewer_name: str,
        reviewer_role: str,
        disposition: str,  # APPROVED / REJECTED / NEEDS_REVISION
        rationale: str,
        inventory: ImpactInventory,
        rule_results: List[RuleResult]
    ) -> ReviewDecision:
        """
        Records human approval decision. Enforces that approval can ONLY succeed
        if all gating conditions are met.
        """
        state, blockers = ReviewWorkflowEngine.evaluate_release_readiness(inventory, rule_results)
        
        conditions_met = (state == ReleaseState.PENDING_HUMAN_APPROVAL)
        
        if disposition == "APPROVED" and not conditions_met:
            raise ValueError(
                f"Cannot approve draft label while release gates are blocked: {'; '.join(blockers)}"
            )

        signature_ref = f"SIG-DEMO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{abs(hash(reviewer_name)) % 10000}"

        return ReviewDecision(
            decision_id=f"DEC-{eco_id}-{variant_id}",
            eco_id=eco_id,
            variant_id=variant_id,
            reviewer_name=reviewer_name,
            reviewer_role=reviewer_role,
            disposition=disposition,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc).isoformat(),
            signature_ref=signature_ref,
            conditions_met=conditions_met
        )
