"""Product and labeling digital thread relationship graph using NetworkX."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import networkx as nx
from src.schemas import TraversalPath


class LabelDigitalThread:
    """
    Constructs and traverses the medical device digital thread relationship graph:
    ECO -> ProductFamily -> SKU -> PackagingLevel -> LabelVariant
    """

    def __init__(self, catalog_path: Optional[str] = None):
        self.graph = nx.DiGraph()
        self.catalog_data: Dict = {}
        if catalog_path:
            self.load_catalog(catalog_path)

    def load_catalog(self, catalog_path: str):
        """Load catalog JSON and build the relationship graph."""
        path = Path(catalog_path)
        with open(path, "r", encoding="utf-8") as f:
            self.catalog_data = json.load(f)
        self.build_graph()

    def build_graph(self, include_broken_edge: bool = False):
        """
        Builds the NetworkX directed graph from catalog entities.
        If include_broken_edge is False, the relationship to LV-ORPHAN-001
        is deliberately severed to demonstrate orphan detection.
        """
        self.graph.clear()

        # 1. Product Family
        pf = self.catalog_data.get("product_family", {})
        pf_id = pf.get("family_id", "PF-CG-01")
        self.graph.add_node(
            pf_id,
            node_type="PRODUCT_FAMILY",
            name=pf.get("name", "CardioGraft Vascular Sealant"),
            sterilization=pf.get("sterilization_type", "EO"),
            applicable_packaging=pf.get("applicable_packaging_levels", ["PRIMARY", "SECONDARY"])
        )

        # 2. Add Variants & Intermediate packaging / SKU nodes
        variants = self.catalog_data.get("variants", [])
        for v in variants:
            v_id = v["variant_id"]
            sku_id = v["sku_id"]
            pkg_level = v["packaging_level"]
            pkg_node_id = f"PKG-{sku_id}-{pkg_level}"
            
            # Add SKU node if not present
            if not self.graph.has_node(sku_id):
                self.graph.add_node(sku_id, node_type="SKU", market=v.get("market"))
                self.graph.add_edge(pf_id, sku_id, relationship="FAMILY_HAS_SKU")

            # Add Packaging Level node if not present
            if not self.graph.has_node(pkg_node_id):
                self.graph.add_node(pkg_node_id, node_type="PACKAGING_LEVEL", level=pkg_level, is_sterile=v.get("is_sterile", False))
                self.graph.add_edge(sku_id, pkg_node_id, relationship="SKU_HAS_PACKAGING")

            # Add Variant node
            self.graph.add_node(
                v_id,
                node_type="LABEL_VARIANT",
                name=v.get("name"),
                packaging_level=pkg_level,
                is_sterile=v.get("is_sterile", False),
                bears_expiry=v.get("bears_expiry", False),
                current_shelf_life=v.get("current_shelf_life")
            )

            # Check if this edge should be connected or severed
            is_connected = v.get("graph_connected", True)
            if is_connected or include_broken_edge:
                self.graph.add_edge(pkg_node_id, v_id, relationship="PACKAGING_HAS_LABEL")
            else:
                # Intentionally omitted graph edge
                pass

    def connect_eco(self, eco_id: str, product_family_id: str):
        """Link an ECO node to the target ProductFamily node."""
        self.graph.add_node(eco_id, node_type="ECO")
        if self.graph.has_node(product_family_id):
            self.graph.add_edge(eco_id, product_family_id, relationship="ECO_TARGETS_FAMILY")

    def forward_traverse(self, eco_id: str) -> Tuple[List[str], Dict[str, TraversalPath]]:
        """
        Traverse forward from the ECO to all reachable LabelVariant nodes.
        Filters for affected variants that bear shelf life / sterile packaging.
        
        Returns:
            (reachable_variant_ids, dict_of_traversal_paths)
        """
        if not self.graph.has_node(eco_id):
            return [], {}

        reachable_variants: List[str] = []
        paths: Dict[str, TraversalPath] = {}

        # Find all reachable nodes from eco_id
        for target_node in nx.descendants(self.graph, eco_id):
            node_data = self.graph.nodes[target_node]
            if node_data.get("node_type") == "LABEL_VARIANT":
                # Check if this label bears expiry / sterile packaging
                if node_data.get("bears_expiry", False) or node_data.get("packaging_level") in ["PRIMARY", "SECONDARY"]:
                    reachable_variants.append(target_node)
                    
                    # Compute shortest path for inspectable provenance
                    try:
                        shortest_path = nx.shortest_path(self.graph, eco_id, target_node)
                        explanation = (
                            f"Graph traversal confirmed: ECO '{eco_id}' -> "
                            f"Family '{shortest_path[1]}' -> "
                            f"SKU '{shortest_path[2]}' -> "
                            f"Packaging '{shortest_path[3]}' -> "
                            f"Label Variant '{target_node}'."
                        )
                        paths[target_node] = TraversalPath(
                            variant_id=target_node,
                            hops=shortest_path,
                            explanation=explanation
                        )
                    except nx.NetworkXNoPath:
                        pass

        reachable_variants.sort()
        return reachable_variants, paths

    def is_variant_connected(self, variant_id: str) -> bool:
        """Check if variant has any in-edges from packaging in the graph."""
        if not self.graph.has_node(variant_id):
            return False
        return self.graph.in_degree(variant_id) > 0
