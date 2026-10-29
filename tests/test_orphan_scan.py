"""Automated tests for uncertainty-aware impact discovery and the scope gate."""

from src.schemas import ScopeDisposition
from src.orphan_scan import InverseCatalogScanner


def test_inverse_scan_surfaces_disconnected_variant(
    catalog_scanner,
    digital_thread,
    extracted_eco
):
    """
    CORE DIFFERENTIATOR ACCEPTANCE TEST:
    Demonstrates that the independent inverse scan detects the candidate
    omitted by ordinary forward traversal.
    """
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, _ = digital_thread.forward_traverse(extracted_eco.eco_id)

    # 1. Forward traversal misses LV-ORPHAN-001
    assert "LV-ORPHAN-001" not in reachable

    # 2. Inverse scan evaluates full catalog metadata
    orphans = catalog_scanner.scan_catalog(extracted_eco, reachable)

    # 3. LV-ORPHAN-001 is surfaced with explicit reason and evidence
    assert len(orphans) == 1
    orphan = orphans[0]
    assert orphan.variant_id == "LV-ORPHAN-001"
    assert orphan.reason == "candidate_match_but_no_graph_path"
    assert orphan.product_family_id == extracted_eco.product_family_id
    assert orphan.disposition == ScopeDisposition.UNRESOLVED
    assert orphan.supporting_evidence["packaging_level"] == "SECONDARY"


def test_connected_variants_not_in_orphan_queue(
    catalog_scanner,
    digital_thread,
    extracted_eco
):
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, _ = digital_thread.forward_traverse(extracted_eco.eco_id)
    orphans = catalog_scanner.scan_catalog(extracted_eco, reachable)

    orphan_ids = {o.variant_id for o in orphans}
    for r_id in reachable:
        assert r_id not in orphan_ids


def test_safe_scope_gate_blocks_until_human_disposition(
    catalog_scanner,
    digital_thread,
    extracted_eco
):
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, _ = digital_thread.forward_traverse(extracted_eco.eco_id)
    inventory = catalog_scanner.build_impact_inventory(extracted_eco, reachable)

    # Gate blocks: scope cannot be complete while orphan is UNRESOLVED
    assert inventory.scope_complete is False
    assert len(inventory.orphan_candidates) == 1
    assert inventory.orphan_candidates[0].disposition == ScopeDisposition.UNRESOLVED

    # Human resolves the orphan
    success = InverseCatalogScanner.update_orphan_disposition(
        inventory=inventory,
        variant_id="LV-ORPHAN-001",
        disposition=ScopeDisposition.AFFECTED,
        reviewer_role="Regulatory Affairs Specialist",
        reviewer_notes="Confirmed procedural kit carton bears sterile expiration date and is in scope."
    )
    assert success is True

    # Gate unblocks: scope is now complete
    assert inventory.scope_complete is True
    assert inventory.orphan_candidates[0].disposition == ScopeDisposition.AFFECTED
    assert inventory.orphan_candidates[0].reviewer_role == "Regulatory Affairs Specialist"
    assert inventory.orphan_candidates[0].disposition_timestamp is not None
