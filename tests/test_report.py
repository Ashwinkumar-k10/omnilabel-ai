"""Automated tests for ground-truth evaluation and evidence reporting."""

from src.report import EvidenceReportGenerator


def test_ground_truth_metrics_evaluation(ground_truth_path, tmp_path):
    generator = EvidenceReportGenerator(ground_truth_path=ground_truth_path)

    # Simulate run matching ground truth targets:
    # 5/5 extracted fields valid, 1/1 orphan surfaced, 5/5 affected variants found,
    # 4/4 critical defects detected, 0/2 benign shifts marked critical, 10/10 audit events valid
    metrics = generator.evaluate_run(
        extracted_fields_valid=5,
        total_extracted_fields=5,
        surfaced_orphans=["LV-ORPHAN-001"],
        total_discovered_affected=[
            "LV-US-STER-001", "LV-EU-STER-001",
            "LV-US-CART-001", "LV-EU-CART-001", "LV-ORPHAN-001"
        ],
        detected_defects=[
            "DEFECT-EXPIRY-MATH", "DEFECT-UDI-CHECKSUM",
            "DEFECT-STERILE-SYMBOL", "DEFECT-PROPAGATION-MISMATCH"
        ],
        benign_changes_marked_critical=0,
        total_benign_changes=2,
        audit_events_valid=10,
        total_audit_events=10
    )

    # Acceptance targets from ground truth manifest
    assert metrics.extraction_exact_match_rate == 1.0
    assert metrics.orphan_candidate_recall == 1.0
    assert metrics.variant_discovery_recall == 1.0
    assert metrics.seeded_critical_defect_recall == 1.0
    assert metrics.false_critical_rate == 0.0
    assert metrics.audit_completeness == 1.0

    # Denominators
    assert metrics.denominators["critical_defects"] == "4/4"
    assert metrics.denominators["orphan_candidates"] == "1/1"
    assert metrics.denominators["variant_discovery"] == "5/5"
    assert metrics.denominators["false_critical"] == "0/2"


def test_export_evidence_artifacts(ground_truth_path, tmp_path):
    generator = EvidenceReportGenerator(ground_truth_path=ground_truth_path)
    metrics = generator.evaluate_run(
        extracted_fields_valid=5,
        total_extracted_fields=5,
        surfaced_orphans=["LV-ORPHAN-001"],
        total_discovered_affected=["LV-US-STER-001", "LV-ORPHAN-001"],
        detected_defects=["DEFECT-EXPIRY-MATH"],
        benign_changes_marked_critical=0,
        total_benign_changes=2,
        audit_events_valid=5,
        total_audit_events=5
    )

    out_dir = tmp_path / "evidence"
    artifacts = generator.export_evidence_package(metrics, output_dir=str(out_dir))

    assert (out_dir / "02_test_manifest.json").exists()
    assert (out_dir / "03_test_results.json").exists()
    assert (out_dir / "test_run_report.json").exists()
