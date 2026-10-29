"""Automated tests for controlled template drafting and visual rendering."""

from src.template_engine import calculate_expiry_date


def test_expiry_date_calculation():
    iso_date, gs1_date = calculate_expiry_date("2026-11-01", 36)
    assert iso_date == "2029-11-01"
    assert gs1_date == "291101"

    iso_date_24, gs1_date_24 = calculate_expiry_date("2026-11-01", 24)
    assert iso_date_24 == "2028-11-01"
    assert gs1_date_24 == "281101"


def test_controlled_candidate_generation(template_engine, baseline_variant_data):
    candidate_data = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )

    # 1. Controlled fields updated
    assert candidate_data["shelf_life_months"] == 36
    assert candidate_data["shelf_life_text"] == "36 Months"
    assert candidate_data["expiry_date"] == "2029-11-01"
    assert "(17)291101" in candidate_data["udi_pi"]
    assert candidate_data["is_draft"] is True
    assert "DRAFT" in candidate_data["revision"]

    # 2. Immutable fields preserved verbatim
    assert candidate_data["lot_number"] == baseline_variant_data["lot_number"]
    assert candidate_data["manufacturer"] == baseline_variant_data["manufacturer"]
    assert candidate_data["udi_di"] == baseline_variant_data["udi_di"]
    assert candidate_data["product_name"] == baseline_variant_data["product_name"]


def test_svg_rendering_and_draft_banner(template_engine, baseline_variant_data):
    candidate_data = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )

    svg_str = template_engine.render_svg("approved_label.svg", candidate_data)
    assert "<svg" in svg_str
    assert "36 Months (USE BY: 2029-11-01)" in svg_str
    assert "CONTROLLED DRAFT — NOT APPROVED" in svg_str
    assert "(17)291101" in svg_str


def test_pixmap_and_pdf_generation(template_engine, baseline_variant_data):
    candidate_data = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )
    svg_str = template_engine.render_svg("approved_label.svg", candidate_data)

    # PNG Pixmap
    png_bytes = template_engine.render_to_png_bytes(svg_str, dpi=100)
    assert len(png_bytes) > 1000
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    # PDF bytes
    pdf_bytes = template_engine.render_to_pdf_bytes(svg_str)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")
