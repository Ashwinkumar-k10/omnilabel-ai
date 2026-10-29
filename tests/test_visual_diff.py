"""Automated tests for visual comparison and finding triage."""

from src.schemas import FindingCategory
from src.visual_diff import VisualDiffEngine


def test_visual_diff_detects_expected_changes(template_engine, baseline_variant_data):
    # 1. Render baseline
    baseline_svg = template_engine.render_svg("approved_label.svg", baseline_variant_data)
    baseline_bytes = template_engine.render_to_png_bytes(baseline_svg, dpi=100)

    # 2. Render candidate
    candidate_data = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )
    candidate_svg = template_engine.render_svg("approved_label.svg", candidate_data)
    candidate_bytes = template_engine.render_to_png_bytes(candidate_svg, dpi=100)

    # 3. Diff
    diff_engine = VisualDiffEngine()
    findings, diff_png, diff_pct = diff_engine.compare_labels(baseline_bytes, candidate_bytes)

    assert diff_pct > 0.0
    assert len(diff_png) > 1000
    assert len(findings) > 0

    # Ensure expected shelf life change is identified
    shelf_findings = [f for f in findings if f.category == FindingCategory.EXPECTED_CHANGE]
    assert len(shelf_findings) > 0


def test_benign_layout_shift_is_not_marked_critical(template_engine, baseline_variant_data):
    """
    CRITICAL ACCEPTANCE TEST:
    A harmless 5px shift in brand logo must be triaged as REVIEW_REQUIRED / benign,
    NOT falsely reported as CRITICAL_RULE_FAILURE (False-critical rate = 0).
    """
    # 1. Render baseline
    baseline_svg = template_engine.render_svg("approved_label.svg", baseline_variant_data)
    baseline_bytes = template_engine.render_to_png_bytes(baseline_svg, dpi=100)

    # 2. Render candidate with benign logo shift
    candidate_data = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )
    benign_candidate_svg = template_engine.render_svg("approved_label.svg", candidate_data, benign_shift=True)
    benign_bytes = template_engine.render_to_png_bytes(benign_candidate_svg, dpi=100)

    # 3. Diff
    diff_engine = VisualDiffEngine()
    findings, _, _ = diff_engine.compare_labels(baseline_bytes, benign_bytes)

    # Check for logo shift finding
    logo_findings = [f for f in findings if "LOGO" in f.finding_id]
    assert len(logo_findings) > 0
    for lf in logo_findings:
        assert lf.category == FindingCategory.REVIEW_REQUIRED
        assert lf.is_benign is True
        # NEVER falsely marked as CRITICAL_RULE_FAILURE
        assert lf.category != FindingCategory.CRITICAL_RULE_FAILURE
