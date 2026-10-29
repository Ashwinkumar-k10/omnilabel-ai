"""Automated tests for human review gating and explicit authorization."""

import pytest
from src.schemas import ReleaseState, ScopeDisposition
from src.orphan_scan import InverseCatalogScanner
from src.rules import execute_all_rules
from src.review import ReviewWorkflowEngine


def test_review_blocks_when_scope_incomplete(
    catalog_scanner,
    digital_thread,
    extracted_eco,
    template_engine,
    baseline_variant_data
):
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, _ = digital_thread.forward_traverse(extracted_eco.eco_id)
    inventory = catalog_scanner.build_impact_inventory(extracted_eco, reachable)

    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )
    rule_results = execute_all_rules(candidate, 36, "36 Months")

    # Release state must be SCOPE_BLOCKED
    state, blockers = ReviewWorkflowEngine.evaluate_release_readiness(inventory, rule_results)
    assert state == ReleaseState.SCOPE_BLOCKED
    assert any("Scope incomplete" in b for b in blockers)

    # Attempting approval while scope is blocked must raise ValueError
    with pytest.raises(ValueError, match="Cannot approve draft label while release gates are blocked"):
        ReviewWorkflowEngine.record_decision(
            eco_id=extracted_eco.eco_id,
            variant_id=baseline_variant_data["variant_id"],
            reviewer_name="Dr. Elena Vance",
            reviewer_role="Senior Packaging Engineer",
            disposition="APPROVED",
            rationale="Attempting premature sign-off",
            inventory=inventory,
            rule_results=rule_results
        )


def test_review_blocks_when_critical_rule_fails(
    catalog_scanner,
    digital_thread,
    extracted_eco,
    template_engine,
    baseline_variant_data
):
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, _ = digital_thread.forward_traverse(extracted_eco.eco_id)
    inventory = catalog_scanner.build_impact_inventory(extracted_eco, reachable)

    # Resolve orphan scope
    InverseCatalogScanner.update_orphan_disposition(
        inventory=inventory,
        variant_id="LV-ORPHAN-001",
        disposition=ScopeDisposition.AFFECTED,
        reviewer_role="Regulatory Affairs Specialist",
        reviewer_notes="Included in scope."
    )

    # Generate candidate with critical defect
    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze.",
        seeded_defect="DEFECT-EXPIRY-MATH"
    )
    rule_results = execute_all_rules(candidate, 36, "36 Months")

    # Release state must be CHECKS_FAILED
    state, blockers = ReviewWorkflowEngine.evaluate_release_readiness(inventory, rule_results)
    assert state == ReleaseState.CHECKS_FAILED
    assert any("RULE-EXPIRY-CALC" in b for b in blockers)


def test_explicit_approval_succeeds_when_all_gates_pass(
    catalog_scanner,
    digital_thread,
    extracted_eco,
    template_engine,
    baseline_variant_data
):
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, _ = digital_thread.forward_traverse(extracted_eco.eco_id)
    inventory = catalog_scanner.build_impact_inventory(extracted_eco, reachable)

    # 1. Resolve scope gate
    InverseCatalogScanner.update_orphan_disposition(
        inventory=inventory,
        variant_id="LV-ORPHAN-001",
        disposition=ScopeDisposition.AFFECTED,
        reviewer_role="Regulatory Affairs Specialist",
        reviewer_notes="Verified and included in change scope."
    )

    # 2. Run clean rules
    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )
    rule_results = execute_all_rules(candidate, 36, "36 Months")

    state, blockers = ReviewWorkflowEngine.evaluate_release_readiness(inventory, rule_results)
    assert state == ReleaseState.PENDING_HUMAN_APPROVAL
    assert blockers == []

    # 3. Explicit qualified human approval
    decision = ReviewWorkflowEngine.record_decision(
        eco_id=extracted_eco.eco_id,
        variant_id=baseline_variant_data["variant_id"],
        reviewer_name="Dr. Sarah Chen",
        reviewer_role="Quality Assurance Director",
        disposition="APPROVED",
        rationale="Verified stability reports TR-2026-881 and compliant UDI barcode syntax.",
        inventory=inventory,
        rule_results=rule_results
    )

    assert decision.disposition == "APPROVED"
    assert decision.conditions_met is True
    assert "SIG-DEMO-" in decision.signature_ref
    assert decision.reviewer_name == "Dr. Sarah Chen"
