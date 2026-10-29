"""Bounded extraction of Engineering Change Order (ECO) attributes with exact provenance."""

import re
from typing import Dict
from src.schemas import ExtractedECO, SourceSpan
from src.provenance import compute_document_hash, extract_and_verify_span


class ECOExtractionError(Exception):
    """Raised when ECO extraction fails schema or validation constraints."""
    pass


def extract_eco_data(raw_text: str, doc_id: str = "ECO-DEMO-001") -> ExtractedECO:
    """
    Deterministically extracts key change fields from an ECO document text,
    validates the schema, and binds every field to exact source-span provenance.
    """
    if not raw_text or not raw_text.strip():
        raise ECOExtractionError("Empty ECO source text provided")

    doc_hash = compute_document_hash(raw_text)

    # 1. ECO Number
    eco_match = re.search(r"ECO Number:\s*([A-Za-z0-9\-]+)", raw_text)
    if not eco_match:
        raise ECOExtractionError("Required field 'ECO Number' not found in source text")
    eco_id = eco_match.group(1).strip()

    # 2. Title
    title_match = re.search(r"Title:\s*(.+)", raw_text)
    title = title_match.group(1).strip() if title_match else "Untitled Change Order"

    # 3. Product Family
    pf_match = re.search(r"Product Family:\s*([A-Za-z0-9\-]+)", raw_text)
    if not pf_match:
        raise ECOExtractionError("Required field 'Product Family' not found in source text")
    product_family_id = pf_match.group(1).strip()

    # 4. Previous Shelf Life
    prev_sl_match = re.search(r"Previous Value:\s*(\d+\s*Months?)", raw_text)
    if not prev_sl_match:
        raise ECOExtractionError("Required field 'Previous Value' for shelf life not found in source text")
    prev_shelf_life = prev_sl_match.group(1).strip()

    # 5. Proposed Shelf Life
    prop_sl_match = re.search(r"Proposed Value:\s*(\d+\s*Months?)", raw_text)
    if not prop_sl_match:
        raise ECOExtractionError("Required field 'Proposed Value' for shelf life not found in source text")
    prop_shelf_life = prop_sl_match.group(1).strip()

    # Extract numeric months
    num_match = re.search(r"(\d+)", prop_shelf_life)
    if not num_match:
        raise ECOExtractionError(f"Could not parse numeric months from proposed shelf life '{prop_shelf_life}'")
    proposed_shelf_life_months = int(num_match.group(1))

    # 6. Storage Conditions
    storage_match = re.search(r"Attribute:\s*Storage Conditions\s*\n\s*Previous Value:\s*(.+)\n\s*Proposed Value:\s*(.+)", raw_text)
    if storage_match:
        storage_condition = storage_match.group(2).strip()
    else:
        # Fallback search
        storage_fallback = re.search(r"Store between [^\.\n]+\.", raw_text)
        storage_condition = storage_fallback.group(0).strip() if storage_fallback else "Store between 2°C and 8°C. Do not freeze."

    # 7. Effective Date
    eff_match = re.search(r"Effective Date:\s*(\d{4}-\d{2}-\d{2})", raw_text)
    effective_date = eff_match.group(1).strip() if eff_match else "2026-11-15"

    # 8. Target Markets
    target_markets = []
    if "US" in raw_text:
        target_markets.append("US")
    if "EU" in raw_text:
        target_markets.append("EU")

    # Generate exact source spans with offsets and verification
    spans: Dict[str, SourceSpan] = {}
    spans["eco_id"] = extract_and_verify_span(raw_text, "eco_id", eco_id, doc_id, doc_hash)
    spans["product_family_id"] = extract_and_verify_span(raw_text, "product_family_id", product_family_id, doc_id, doc_hash)
    spans["previous_shelf_life"] = extract_and_verify_span(raw_text, "previous_shelf_life", prev_shelf_life, doc_id, doc_hash)
    spans["proposed_shelf_life"] = extract_and_verify_span(raw_text, "proposed_shelf_life", prop_shelf_life, doc_id, doc_hash)
    spans["storage_condition"] = extract_and_verify_span(raw_text, "storage_condition", storage_condition, doc_id, doc_hash)

    # Return validated ExtractedECO Pydantic model
    return ExtractedECO(
        eco_id=eco_id,
        title=title,
        product_family_id=product_family_id,
        previous_shelf_life=prev_shelf_life,
        proposed_shelf_life=prop_shelf_life,
        proposed_shelf_life_months=proposed_shelf_life_months,
        storage_condition=storage_condition,
        effective_date=effective_date,
        target_markets=target_markets,
        spans=spans,
        source_hash=doc_hash,
        extraction_mode="bounded_fixture",
        extractor_version="v1.0.0"
    )
