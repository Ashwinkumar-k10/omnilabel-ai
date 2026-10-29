"""Automated tests for deterministic labeling rules and seeded defect detection."""

from src.schemas import FindingCategory
from src.rules import (
    calculate_gs1_check_digit,
    check_udi_syntax,
    check_expiry_calculation,
    check_sterile_barrier_symbol,
    check_eco_propagation,
    execute_all_rules
)


def test_gs1_check_digit_calculation():
    # Known GTIN check digit tests:
    # "629104150021" -> check digit is 3 (GS1 official specification benchmark)
    assert calculate_gs1_check_digit("629104150021") == 3
    # "0085001234567" -> check digit is 1
    assert calculate_gs1_check_digit("0085001234567") == 1
    # "0085001234568" -> check digit is 8
    assert calculate_gs1_check_digit("0085001234568") == 8


def test_valid_candidate_passes_all_rules(template_engine, baseline_variant_data):
    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze."
    )
    results = execute_all_rules(candidate, 36, "36 Months")
    assert all(r.status == "PASS" for r in results)


def test_seeded_defect_01_expiry_math(template_engine, baseline_variant_data):
    """SEEDED DEFECT 1: Expiry date arithmetic mismatch."""
    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze.",
        seeded_defect="DEFECT-EXPIRY-MATH"
    )
    result = check_expiry_calculation(candidate)
    assert result.status == "FAIL"
    assert result.category == FindingCategory.CRITICAL_RULE_FAILURE
    assert "Arithmetic inconsistency" in result.message


def test_seeded_defect_02_udi_checksum(template_engine, baseline_variant_data):
    """SEEDED DEFECT 2: UDI-DI check digit corruption."""
    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze.",
        seeded_defect="DEFECT-UDI-CHECKSUM"
    )
    result = check_udi_syntax(candidate)
    assert result.status == "FAIL"
    assert result.category == FindingCategory.CRITICAL_RULE_FAILURE
    assert "check digit mismatch" in result.message


def test_seeded_defect_03_sterile_symbol(template_engine, baseline_variant_data):
    """SEEDED DEFECT 3: Missing ISO 15223-1 sterile symbol on primary barrier."""
    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze.",
        seeded_defect="DEFECT-STERILE-SYMBOL"
    )
    result = check_sterile_barrier_symbol(candidate)
    assert result.status == "FAIL"
    assert result.category == FindingCategory.CRITICAL_RULE_FAILURE
    assert "sterile barrier packaging requires explicit ISO 15223-1 sterile symbol" in result.message


def test_seeded_defect_04_eco_propagation_mismatch(template_engine, baseline_variant_data):
    """SEEDED DEFECT 4: Candidate retained unapproved legacy 24-Month value."""
    candidate = template_engine.generate_candidate_data(
        baseline_data=baseline_variant_data,
        proposed_shelf_life_months=36,
        proposed_shelf_life_text="36 Months",
        storage_condition="Store between 2°C and 8°C. Do not freeze.",
        seeded_defect="DEFECT-PROPAGATION-MISMATCH"
    )
    result = check_eco_propagation(candidate, 36, "36 Months")
    assert result.status == "FAIL"
    assert result.category == FindingCategory.CRITICAL_RULE_FAILURE
    assert "ECO change propagation failed" in result.message
