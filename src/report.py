"""Ground-truth evaluation and evidence reporting engine for OmniLabel AI."""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from src.schemas import EvaluationMetrics


class EvidenceReportGenerator:
    """Computes exact metrics against ground truth manifest and produces evidence packages."""

    def __init__(self, ground_truth_path: str = "data/ground_truth.json"):
        self.gt_path = Path(ground_truth_path)
        with open(self.gt_path, "r", encoding="utf-8") as f:
            self.ground_truth: Dict[str, Any] = json.load(f)

    def evaluate_run(
        self,
        extracted_fields_valid: int,
        total_extracted_fields: int,
        surfaced_orphans: List[str],
        total_discovered_affected: List[str],
        detected_defects: List[str],
        benign_changes_marked_critical: int,
        total_benign_changes: int,
        audit_events_valid: int,
        total_audit_events: int
    ) -> EvaluationMetrics:
        """Computes exact metrics with explicit numerators and denominators."""
        gt_portfolio = self.ground_truth.get("portfolio", {})
        gt_affected = gt_portfolio.get("affected_variants", [])
        gt_orphans = gt_portfolio.get("expected_orphan_scan_candidates", [])
        gt_defects = self.ground_truth.get("seeded_critical_defects", [])

        # 1. Extraction exact match rate
        ext_rate = (extracted_fields_valid / total_extracted_fields) if total_extracted_fields > 0 else 0.0

        # 2. Orphan candidate recall
        orphans_found = sum(1 for o in gt_orphans if o in surfaced_orphans)
        orphan_recall = (orphans_found / len(gt_orphans)) if gt_orphans else 1.0

        # 3. Variant discovery recall
        variants_found = sum(1 for v in gt_affected if v in total_discovered_affected)
        variant_recall = (variants_found / len(gt_affected)) if gt_affected else 1.0

        # 4. Seeded critical-defect recall
        defects_detected = sum(1 for d in gt_defects if d["defect_id"] in detected_defects or d["rule_id"] in detected_defects)
        defect_recall = (defects_detected / len(gt_defects)) if gt_defects else 1.0

        # 5. False-critical rate
        false_crit_rate = (benign_changes_marked_critical / total_benign_changes) if total_benign_changes > 0 else 0.0

        # 6. Audit completeness
        audit_comp = (audit_events_valid / total_audit_events) if total_audit_events > 0 else 1.0

        denominators = {
            "extraction_fields": f"{extracted_fields_valid}/{total_extracted_fields}",
            "orphan_candidates": f"{orphans_found}/{len(gt_orphans)}",
            "variant_discovery": f"{variants_found}/{len(gt_affected)}",
            "critical_defects": f"{defects_detected}/{len(gt_defects)}",
            "false_critical": f"{benign_changes_marked_critical}/{total_benign_changes}",
            "audit_events": f"{audit_events_valid}/{total_audit_events}"
        }

        return EvaluationMetrics(
            seeded_critical_defect_recall=defect_recall,
            orphan_candidate_recall=orphan_recall,
            variant_discovery_recall=variant_recall,
            extraction_exact_match_rate=ext_rate,
            false_critical_rate=false_crit_rate,
            audit_completeness=audit_comp,
            denominators=denominators,
            software_version="1.0.0",
            evaluation_timestamp=datetime.now(timezone.utc).isoformat()
        )

    def export_evidence_package(
        self,
        metrics: EvaluationMetrics,
        output_dir: str = "evidence"
    ) -> Dict[str, str]:
        """Saves machine-readable evidence files into the evidence folder."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        manifest_file = out_path / "02_test_manifest.json"
        results_file = out_path / "03_test_results.json"
        summary_file = out_path / "test_run_report.json"

        # 1. Save test manifest copy
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(self.ground_truth, f, indent=2)

        # 2. Save test results
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(metrics.model_dump(), f, indent=2)

        # 3. Save run report summary
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "report_title": "OmniLabel AI - Ground Truth Validation Run Report",
                "timestamp": metrics.evaluation_timestamp,
                "version": metrics.software_version,
                "metrics": metrics.model_dump()
            }, f, indent=2)

        return {
            "test_manifest": str(manifest_file),
            "test_results": str(results_file),
            "run_report": str(summary_file)
        }

    def generate_compliance_summary_markdown(self, metrics: EvaluationMetrics) -> str:
        """Generates a formatted markdown compliance summary for regulatory filings."""
        return (
            f"# OmniLabel AI — Verification Report\n\n"
            f"- **Evaluated:** {metrics.evaluation_timestamp}\n"
            f"- **Software Version:** {metrics.software_version}\n"
            f"- **Orphan-Candidate Recall:** {metrics.orphan_candidate_recall * 100:.1f}%\n"
            f"- **Variant Discovery Recall:** {metrics.variant_discovery_recall * 100:.1f}%\n"
            f"- **Critical Defect Recall:** {metrics.seeded_critical_defect_recall * 100:.1f}%\n"
            f"- **False-Critical Rate:** {metrics.false_critical_rate * 100:.1f}%\n"
            f"- **Cryptographic Audit Completeness:** {metrics.audit_completeness * 100:.1f}%\n"
        )

