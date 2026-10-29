"""Automated tests for bounded ECO extraction and exact source-span provenance."""

import pytest
from src.extraction import extract_eco_data, ECOExtractionError
from src.provenance import verify_source_span, extract_and_verify_span, compute_document_hash


def test_extract_valid_eco(eco_demo_text):
    eco = extract_eco_data(eco_demo_text, doc_id="ECO-DEMO-001")
    assert eco.eco_id == "ECO-DEMO-001"
    assert eco.product_family_id == "PF-CG-01"
    assert eco.previous_shelf_life == "24 Months"
    assert eco.proposed_shelf_life == "36 Months"
    assert eco.proposed_shelf_life_months == 36
    assert "Store between 2°C and 8°C" in eco.storage_condition
    assert eco.effective_date == "2026-11-15"
    assert "US" in eco.target_markets
    assert "EU" in eco.target_markets


def test_exact_source_spans_match(eco_demo_text):
    eco = extract_eco_data(eco_demo_text, doc_id="ECO-DEMO-001")
    
    # Check that every extracted span points to the exact substring in the source
    for field_name, span in eco.spans.items():
        assert span.is_verified is True
        assert span.start_char >= 0
        assert span.end_char > span.start_char
        source_slice = eco_demo_text[span.start_char:span.end_char]
        assert source_slice == span.value
        assert span.exact_text == span.value


def test_tampered_span_detected(eco_demo_text):
    eco = extract_eco_data(eco_demo_text, doc_id="ECO-DEMO-001")
    shelf_span = eco.spans["proposed_shelf_life"]
    
    # Tamper with the expected value
    is_valid, slice_text, msg = verify_source_span(
        eco_demo_text,
        shelf_span.start_char,
        shelf_span.end_char,
        expected_value="48 Months"  # Tampered / Fabricated
    )
    assert is_valid is False
    assert "Span mismatch" in msg
    assert slice_text == "36 Months"


def test_invalid_span_bounds():
    is_valid, slice_text, msg = verify_source_span(
        "Small text",
        start_char=50,
        end_char=100,
        expected_value="test"
    )
    assert is_valid is False
    assert "Invalid span bounds" in msg


def test_fabricated_substring_rejected(eco_demo_text):
    doc_hash = compute_document_hash(eco_demo_text)
    span = extract_and_verify_span(
        eco_demo_text,
        field_name="unsupported_claim",
        target_substring="100% cure rate guaranteed",
        doc_id="ECO-DEMO-001",
        doc_hash=doc_hash
    )
    assert span.is_verified is False
    assert span.start_char == -1
    assert "not found in source text" in span.verification_message


def test_invalid_eco_raises(eco_invalid_text):
    with pytest.raises(ECOExtractionError):
        extract_eco_data(eco_invalid_text, doc_id="ECO-INVALID-001")


def test_empty_input_raises():
    with pytest.raises(ECOExtractionError):
        extract_eco_data("", doc_id="EMPTY")
