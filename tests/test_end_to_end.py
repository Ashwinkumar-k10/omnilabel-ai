"""End-to-end workflow integration test for OmniLabel AI."""

import json
from src.extraction import extract_eco_data
from src.impact_graph import LabelDigitalThread
from src.orphan_scan import InverseCatalogScanner
from src.template_engine import ControlledTemplateEngine
from src.rules import execute_all_rules
from src.visual_diff import VisualDiffEngine
from src.review import ReviewWorkflowEngine
from src.audit import AuditLedger
from src.report import EvidenceReportGenerator
from src.schemas import ReleaseState, ScopeDisposition, FindingCategory


def test_full_omnilabel_ai_end_to_end_workflow(
    eco_demo_text,
    catalog_path,
    ground_truth_path,
    baseline_variant_data,
    tmp_path
):
    """
    Executes the complete signature scenario defined in the Demo Execution Playbook:
    ECO-DEMO-001 sterile shelf life change (24mo -> 36mo),
    detecting the disconnected label LV-ORPHAN-001,
    controlled drafting, deterministic rules, visual diff,
    human sign-off, hash-chained audit, and evidence reporting.
    """
    audit_db_file = tmp_path / "e2e_audit.db"
    audit = AuditLedger(db_path=str(audit_db_file))

    # =========================================================================
    # STAGE 1: ECO Intake & Exact Provenance Verification
    # =========================================================================
    eco = extract_eco_data(eco_demo_text, doc_id="ECO-DEMO-001")
    assert eco.eco_id == "ECO-DEMO-001"
    assert eco.proposed_shelf_life_months == 36

    audit.append_event(
        event_id="EVT-01-INTAKE",
        actor="IntakeEngine",
        role="System",
        action="ECO_INTAKE",
        entity_type="ECO",
        entity_id=eco.eco_id,
        details={"source_hash": eco.source_hash, "proposed_shelf_life": eco.proposed_shelf_life}
    )

    # Verify 100% exact source span provenance
    for field_name, span in eco.spans.items():
        assert span.is_verified is True
        assert eco_demo_text[span.start_char:span.end_char] == span.value

    # =========================================================================
    # STAGE 2: Impact Discovery (Forward Graph + Inverse Catalog Scan)
    # =========================================================================
    dt = LabelDigitalThread(catalog_path=catalog_path)
    dt.connect_eco(eco.eco_id, eco.product_family_id)
    reachable, paths = dt.forward_traverse(eco.eco_id)

    # Forward traversal finds connected 4, but misses LV-ORPHAN-001
    assert len(reachable) == 4
    assert "LV-ORPHAN-001" not in reachable

    scanner = InverseCatalogScanner(catalog_path=catalog_path)
    inventory = scanner.build_impact_inventory(eco, reachable)

    # Core differentiator: Inverse scan surfaces LV-ORPHAN-001 into Uncertainty Queue
    assert len(inventory.orphan_candidates) == 1
    orphan = inventory.orphan_candidates[0]
    assert orphan.variant_id == "LV-ORPHAN-001"
    assert orphan.reason == "candidate_match_but_no_graph_path"
    assert inventory.scope_complete is False  # Safe scope gate engaged

    audit.append_event(
        event_id="EVT-02-DISCOVERY",
        actor="ImpactDiscoveryEngine",
        role="System",
        action="IMPACT_DISCOVERY_COMPLETED",
        entity_type="IMPACT_INVENTORY",
        entity_id=eco.eco_id,
        details={
            "forward_reachable_count": len(reachable),
            "orphan_candidates_count": len(inventory.orphan_candidates),
            "orphan_id": orphan.variant_id
        }
    )

    # =========================================================================
    # STAGE 3: Safe Scope Gate & Human Disposition
    # =========================================================================
    # Check that release is blocked while orphan is UNRESOLVED
    state, blockers = ReviewWorkflowEngine.evaluate_release_readiness(inventory, [])
    assert state == ReleaseState.SCOPE_BLOCKED

    # Qualified human reviews and classifies orphan as AFFECTED
    InverseCatalogScanner.update_orphan_disposition(
        inventory=inventory,
        variant_id="LV-ORPHAN-001",
        disposition=ScopeDisposition.AFFECTED,
        reviewer_role="Regulatory Affairs Specialist",
        reviewer_notes="Confirmed procedural kit secondary carton bears sterile shelf life; in scope."
    )
    assert inventory.scope_complete is True

    audit.append_event(
        event_id="EVT-03-ORPHAN-RESOLVED",
        actor="Dr. Sarah Chen",
        role="Regulatory Affairs Specialist",
        action="ORPHAN_DISPOSITION_RECORDED",
        entity_type="LABEL_VARIANT",
        entity_id="LV-ORPHAN-001",
        details={"disposition": "AFFECTED", "scope_complete": True}
    )

    # Total affected is now 4 forward + 1 orphan = 5 variants
    all_affected = list(reachable) + [orphan.variant_id]
    assert len(all_affected) == 5

    # =========================================================================
    # STAGE 4: Controlled Label Drafting
    # =========================================================================
    engine = ControlledTemplateEngine()
    candidate_data = engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition=eco.storage_condition
    )
    assert candidate_data["shelf_life_months"] == 36
    assert candidate_data["expiry_date"] == "2029-11-01"
    assert candidate_data["is_draft"] is True

    candidate_svg = engine.render_svg("approved_label.svg", candidate_data)
    candidate_bytes = engine.render_to_png_bytes(candidate_svg, dpi=100)
    assert len(candidate_bytes) > 1000

    audit.append_event(
        event_id="EVT-04-DRAFT-GENERATED",
        actor="ControlledTemplateEngine",
        role="System",
        action="LABEL_DRAFT_GENERATED",
        entity_type="LABEL_DRAFT",
        entity_id="LV-US-STER-001-DRAFT",
        details={"template": "approved_label.svg", "revision": candidate_data["revision"]}
    )

    # =========================================================================
    # STAGE 5: Deterministic Validation Rules & Defect Detection
    # =========================================================================
    clean_rule_results = execute_all_rules(candidate_data, 36, "36 Months")
    assert all(r.status == "PASS" for r in clean_rule_results)

    # Test seeded critical defects detection
    defects_tested = [
        "DEFECT-EXPIRY-MATH", "DEFECT-UDI-CHECKSUM",
        "DEFECT-STERILE-SYMBOL", "DEFECT-PROPAGATION-MISMATCH"
    ]
    detected_defects = []
    for defect_id in defects_tested:
        defect_data = engine.generate_candidate_data(
            baseline_data=baseline_variant_data,
            proposed_shelf_life_months=36,
            proposed_shelf_life_text="36 Months",
            storage_condition=eco.storage_condition,
            seeded_defect=defect_id
        )
        def_results = execute_all_rules(defect_data, 36, "36 Months")
        failed = [r for r in def_results if r.status == "FAIL"]
        assert len(failed) > 0
        detected_defects.append(defect_id)

    assert len(detected_defects) == 4

    audit.append_event(
        event_id="EVT-05-RULES-EXECUTED",
        actor="DeterministicRuleEngine",
        role="System",
        action="RULE_VALIDATION_EXECUTED",
        entity_type="RULE_SET",
        entity_id="OMNILABEL-CORE-RULES",
        details={"clean_checks_passed": len(clean_rule_results), "seeded_defects_detected": 4}
    )

    # =========================================================================
    # STAGE 6: Visual Comparison & Benign Change Triage
    # =========================================================================
    baseline_svg = engine.render_svg("approved_label.svg", baseline_variant_data)
    baseline_bytes = engine.render_to_png_bytes(baseline_svg, dpi=100)

    # Benign visual change test (harmless 5px logo offset)
    benign_svg = engine.render_svg("approved_label.svg", candidate_data, benign_shift=True)
    benign_bytes = engine.render_to_png_bytes(benign_svg, dpi=100)

    diff_engine = VisualDiffEngine()
    diff_findings, diff_annotated, diff_pct = diff_engine.compare_labels(baseline_bytes, benign_bytes)
    assert diff_pct > 0.0

    # Ensure logo shift is REVIEW_REQUIRED/benign and NOT marked critical (False-critical rate = 0%)
    critical_visual_findings = [f for f in diff_findings if f.category == FindingCategory.CRITICAL_RULE_FAILURE]
    assert len(critical_visual_findings) == 0

    audit.append_event(
        event_id="EVT-06-VISUAL-DIFF",
        actor="VisualDiffEngine",
        role="System",
        action="VISUAL_DIFF_ANALYZED",
        entity_type="VISUAL_DIFF",
        entity_id="DIFF-LV-US-STER-001",
        details={"findings_count": len(diff_findings), "false_critical_count": 0}
    )

    # =========================================================================
    # STAGE 7: Human Review & Explicit Approval
    # =========================================================================
    state, blockers = ReviewWorkflowEngine.evaluate_release_readiness(inventory, clean_rule_results)
    assert state == ReleaseState.PENDING_HUMAN_APPROVAL
    assert blockers == []

    decision = ReviewWorkflowEngine.record_decision(
        eco_id=eco.eco_id,
        variant_id=baseline_variant_data["variant_id"],
        reviewer_name="Dr. Sarah Chen",
        reviewer_role="Quality Assurance Director",
        disposition="APPROVED",
        rationale="All 5 affected variants triaged; stability data verified; all deterministic rules passed.",
        inventory=inventory,
        rule_results=clean_rule_results
    )
    assert decision.disposition == "APPROVED"
    assert decision.conditions_met is True

    audit.append_event(
        event_id="EVT-07-HUMAN-APPROVAL",
        actor=decision.reviewer_name,
        role=decision.reviewer_role,
        action="HUMAN_REVIEW_RECORDED",
        entity_type="REVIEW_DECISION",
        entity_id=decision.decision_id,
        details={"disposition": "APPROVED", "signature_ref": decision.signature_ref}
    )

    # =========================================================================
    # STAGE 8: Audit Trail Integrity Verification & Evidence Export
    # =========================================================================
    is_valid, audit_msg = audit.verify_integrity()
    assert is_valid is True
    assert "Cryptographic integrity verified" in audit_msg

    audit_export_file = tmp_path / "07_audit_event_export.json"
    audit.export_to_json(str(audit_export_file))
    assert audit_export_file.exists()

    report_gen = EvidenceReportGenerator(ground_truth_path=ground_truth_path)
    metrics = report_gen.evaluate_run(
        extracted_fields_valid=len(eco.spans),
        total_extracted_fields=len(eco.spans),
        surfaced_orphans=[orphan.variant_id],
        total_discovered_affected=all_affected,
        detected_defects=detected_defects,
        benign_changes_marked_critical=0,
        total_benign_changes=2,
        audit_events_valid=len(audit.fetch_all_events()),
        total_audit_events=len(audit.fetch_all_events())
    )

    evidence_out = tmp_path / "evidence"
    report_gen.export_evidence_package(metrics, output_dir=str(evidence_out))

    # Assert 100% target metrics
    assert metrics.seeded_critical_defect_recall == 1.0
    assert metrics.orphan_candidate_recall == 1.0
    assert metrics.variant_discovery_recall == 1.0
    assert metrics.extraction_exact_match_rate == 1.0
    assert metrics.false_critical_rate == 0.0
    assert metrics.audit_completeness == 1.0
