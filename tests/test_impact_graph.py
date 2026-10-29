"""Automated tests for the product/variant digital thread relationship graph."""

from src.impact_graph import LabelDigitalThread


def test_graph_construction(digital_thread):
    # Verify graph contains nodes
    assert digital_thread.graph.has_node("PF-CG-01")
    assert digital_thread.graph.has_node("SKU-CG-US-01")
    assert digital_thread.graph.has_node("LV-US-STER-001")
    assert digital_thread.graph.has_node("LV-ORPHAN-001")


def test_forward_traversal_finds_connected_variants(digital_thread, extracted_eco):
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, paths = digital_thread.forward_traverse(extracted_eco.eco_id)

    # 4 connected affected packaging variants
    expected_reachable = [
        "LV-EU-CART-001",
        "LV-EU-STER-001",
        "LV-US-CART-001",
        "LV-US-STER-001"
    ]
    assert reachable == expected_reachable

    # Check that each reachable variant has an inspectable traversal path
    for v_id in reachable:
        assert v_id in paths
        path_info = paths[v_id]
        assert len(path_info.hops) >= 4
        assert path_info.hops[0] == extracted_eco.eco_id
        assert path_info.hops[-1] == v_id
        assert "Graph traversal confirmed" in path_info.explanation


def test_severed_edge_variant_is_missed_by_forward_traversal(digital_thread, extracted_eco):
    """
    CRITICAL ACCEPTANCE TEST:
    Verifies that the deliberately orphaned variant LV-ORPHAN-001
    is NOT reachable via forward graph traversal because its relationship edge was severed.
    """
    digital_thread.connect_eco(extracted_eco.eco_id, extracted_eco.product_family_id)
    reachable, _ = digital_thread.forward_traverse(extracted_eco.eco_id)

    assert "LV-ORPHAN-001" not in reachable
    assert digital_thread.is_variant_connected("LV-ORPHAN-001") is False


def test_nonexistent_eco_traversal(digital_thread):
    reachable, paths = digital_thread.forward_traverse("ECO-NON-EXISTENT")
    assert reachable == []
    assert paths == {}
