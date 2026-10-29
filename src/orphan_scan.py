"""Uncertainty-Aware Impact Discovery: Independent Inverse Catalog Scanner & Scope Gate."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from src.schemas import (
    CatalogVariant,
    OrphanCandidate,
    ScopeDisposition,
    ImpactInventory,
    ExtractedECO
)


class InverseCatalogScanner:
    """
    Scans the master label catalog independently of graph edges to detect
    potentially affected label variants whose relationships were dropped or omitted.
    """

    def __init__(self, catalog_path: Optional[str] = None):
        self.catalog_variants: List[CatalogVariant] = []
        if catalog_path:
            self.load_catalog(catalog_path)

    def load_catalog(self, catalog_path: str):
        path = Path(catalog_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.catalog_variants = [CatalogVariant(**v) for v in data.get("variants", [])]

    def scan_catalog(
        self,
        eco: ExtractedECO,
        forward_reachable_variants: List[str]
    ) -> List[OrphanCandidate]:
        """
        Compares ECO change criteria against catalog variant metadata.
        Surfaces any variant matching applicability criteria that was omitted from forward traversal.
        """
        candidates: List[OrphanCandidate] = []
        forward_set = set(forward_reachable_variants)

        for variant in self.catalog_variants:
            # Check 1: Does this variant belong to the ECO target product family?
            is_same_family = (variant.product_family_id == eco.product_family_id)
            
            # Check 2: Does it have sterile / shelf-life / primary or secondary packaging attributes?
            is_affected_tier = variant.packaging_level in ["PRIMARY", "SECONDARY"]
            has_expiry_attribute = variant.bears_expiry or (variant.current_shelf_life is not None)

            if is_same_family and is_affected_tier and has_expiry_attribute:
                # If it should be affected, check if it was reached by the graph traversal
                if variant.variant_id not in forward_set:
                    # SURFACED ORPHAN CANDIDATE!
                    candidate = OrphanCandidate(
                        variant_id=variant.variant_id,
                        name=variant.name,
                        product_family_id=variant.product_family_id,
                        sku_id=variant.sku_id,
                        packaging_level=variant.packaging_level,
                        reason="candidate_match_but_no_graph_path",
                        supporting_evidence={
                            "matched_product_family": variant.product_family_id,
                            "packaging_level": variant.packaging_level,
                            "is_sterile": variant.is_sterile,
                            "current_shelf_life": variant.current_shelf_life,
                            "catalog_severed_note": variant.severed_edge_reason or "Missing graph link in PLM digital thread"
                        },
                        disposition=ScopeDisposition.UNRESOLVED
                    )
                    candidates.append(candidate)

        return candidates

    def build_impact_inventory(
        self,
        eco: ExtractedECO,
        forward_reachable: List[str]
    ) -> ImpactInventory:
        """Constructs the complete tri-state impact inventory."""
        orphans = self.scan_catalog(eco, forward_reachable)
        
        # Determine unaffected variants from catalog
        affected_set = set(forward_reachable).union({o.variant_id for o in orphans})
        unaffected = [
            v.variant_id for v in self.catalog_variants
            if v.variant_id not in affected_set
        ]

        # Scope is incomplete as long as any orphan candidate remains UNRESOLVED
        scope_complete = len(orphans) == 0 or all(
            o.disposition != ScopeDisposition.UNRESOLVED for o in orphans
        )

        summary = (
            f"Impact inventory: {len(forward_reachable)} forward-connected affected, "
            f"{len(orphans)} orphan candidate(s) in uncertainty queue, "
            f"{len(unaffected)} confirmed unaffected."
        )

        return ImpactInventory(
            eco_id=eco.eco_id,
            forward_reachable_variants=sorted(forward_reachable),
            orphan_candidates=orphans,
            unaffected_variants=sorted(unaffected),
            scope_complete=scope_complete,
            total_in_portfolio=len(self.catalog_variants),
            summary=summary
        )

    @staticmethod
    def update_orphan_disposition(
        inventory: ImpactInventory,
        variant_id: str,
        disposition: ScopeDisposition,
        reviewer_role: str,
        reviewer_notes: str
    ) -> bool:
        """
        Updates the human disposition on an orphan candidate.
        Recalculates scope_complete gate status.
        """
        for orphan in inventory.orphan_candidates:
            if orphan.variant_id == variant_id:
                orphan.disposition = disposition
                orphan.reviewer_role = reviewer_role
                orphan.reviewer_notes = reviewer_notes
                orphan.disposition_timestamp = datetime.now(timezone.utc).isoformat()
                
                # Check gate
                inventory.scope_complete = all(
                    o.disposition != ScopeDisposition.UNRESOLVED 
                    for o in inventory.orphan_candidates
                )
                return True
        return False
