"""Deterministic validation rule engine for regulated medical device labeling."""

import re
from datetime import datetime
from typing import Dict, Any, List
from src.schemas import RuleResult, RuleSeverity, FindingCategory


def calculate_gs1_check_digit(number_str: str) -> int:
    """
    Computes GS1 Modulo-10 check digit for GTIN strings (e.g. 13 or 14 digits).
    For a 14-digit GTIN without the last check digit (first 13 digits):
    Weights from right to left alternate 3, 1, 3, 1...
    """
    digits = [int(c) for c in number_str if c.isdigit()]
    if not digits:
        return -1
    
    # Process from right to left of the payload (excluding check digit)
    # The digit immediately preceding the check digit has multiplier 3
    total = 0
    multiplier = 3
    for d in reversed(digits):
        total += d * multiplier
        multiplier = 1 if multiplier == 3 else 3
        
    remainder = total % 10
    return (10 - remainder) % 10


def check_udi_syntax(label_data: Dict[str, Any]) -> RuleResult:
    """
    RULE-UDI-SYNTAX: Validates GS1 UDI format and GTIN-14 check digit algorithm.
    """
    udi_di = label_data.get("udi_di", "")
    full_udi = label_data.get("full_udi", "")
    
    # Check DI length (14 digits)
    if not re.match(r"^\d{14}$", udi_di):
        return RuleResult(
            rule_id="RULE-UDI-SYNTAX",
            rule_name="GS1 UDI Device Identifier Syntax & Structure",
            version="v2.1.0",
            severity=RuleSeverity.CRITICAL,
            status="FAIL",
            category=FindingCategory.CRITICAL_RULE_FAILURE,
            message=f"UDI-DI '{udi_di}' is not a valid 14-digit GTIN numeric string.",
            expected="14-digit numeric GTIN",
            actual=udi_di,
            executed=True,
            test_ref="TC-UDI-01"
        )
        
    # Check Mod-10 checksum
    payload = udi_di[:13]
    actual_check_digit = int(udi_di[13])
    calculated_check_digit = calculate_gs1_check_digit(payload)
    
    if actual_check_digit != calculated_check_digit:
        return RuleResult(
            rule_id="RULE-UDI-SYNTAX",
            rule_name="GS1 UDI Device Identifier Syntax & Structure",
            version="v2.1.0",
            severity=RuleSeverity.CRITICAL,
            status="FAIL",
            category=FindingCategory.CRITICAL_RULE_FAILURE,
            message=(
                f"UDI-DI check digit mismatch: last digit is '{actual_check_digit}', "
                f"but calculated GS1 Mod-10 check digit is '{calculated_check_digit}'."
            ),
            expected=f"Checksum {calculated_check_digit}",
            actual=f"Checksum {actual_check_digit}",
            executed=True,
            test_ref="TC-UDI-01"
        )
        
    return RuleResult(
        rule_id="RULE-UDI-SYNTAX",
        rule_name="GS1 UDI Device Identifier Syntax & Structure",
        version="v2.1.0",
        severity=RuleSeverity.CRITICAL,
        status="PASS",
        category=FindingCategory.EXPECTED_CHANGE,
        message=f"UDI-DI '{udi_di}' conforms to GS1 GTIN-14 specification with valid Mod-10 check digit.",
        expected="Valid GTIN-14",
        actual=udi_di,
        executed=True,
        test_ref="TC-UDI-01"
    )


def check_expiry_calculation(label_data: Dict[str, Any]) -> RuleResult:
    """
    RULE-EXPIRY-CALC: Validates arithmetic consistency between manufacturing date,
    shelf life duration, and the printed expiry date.
    """
    mfg_date_str = label_data.get("mfg_date")
    expiry_date_str = label_data.get("expiry_date")
    shelf_life_months = label_data.get("shelf_life_months")
    
    if not mfg_date_str or not expiry_date_str or shelf_life_months is None:
        return RuleResult(
            rule_id="RULE-EXPIRY-CALC",
            rule_name="Sterile Shelf Life Expiry Arithmetic Consistency",
            version="v1.4.0",
            severity=RuleSeverity.CRITICAL,
            status="FAIL",
            category=FindingCategory.CRITICAL_RULE_FAILURE,
            message="Missing manufacturing date, expiry date, or shelf life months parameter.",
            executed=True,
            test_ref="TC-EXP-01"
        )
        
    try:
        mfg_dt = datetime.strptime(mfg_date_str, "%Y-%m-%d")
        exp_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d")
    except ValueError as e:
        return RuleResult(
            rule_id="RULE-EXPIRY-CALC",
            rule_name="Sterile Shelf Life Expiry Arithmetic Consistency",
            version="v1.4.0",
            severity=RuleSeverity.CRITICAL,
            status="FAIL",
            category=FindingCategory.CRITICAL_RULE_FAILURE,
            message=f"Date parsing error: {e}",
            executed=True,
            test_ref="TC-EXP-01"
        )

    # Calculate expected expiry
    total_months = mfg_dt.month + shelf_life_months
    expected_year = mfg_dt.year + (total_months - 1) // 12
    expected_month = ((total_months - 1) % 12) + 1
    expected_day = min(mfg_dt.day, 28) if expected_month == 2 else min(mfg_dt.day, 30) if expected_month in [4, 6, 9, 11] else mfg_dt.day
    expected_exp_str = datetime(expected_year, expected_month, expected_day).strftime("%Y-%m-%d")

    if expiry_date_str != expected_exp_str:
        return RuleResult(
            rule_id="RULE-EXPIRY-CALC",
            rule_name="Sterile Shelf Life Expiry Arithmetic Consistency",
            version="v1.4.0",
            severity=RuleSeverity.CRITICAL,
            status="FAIL",
            category=FindingCategory.CRITICAL_RULE_FAILURE,
            message=(
                f"Arithmetic inconsistency: MFG '{mfg_date_str}' + {shelf_life_months} months "
                f"should expire on '{expected_exp_str}', but label states '{expiry_date_str}'."
            ),
            expected=expected_exp_str,
            actual=expiry_date_str,
            executed=True,
            test_ref="TC-EXP-01"
        )

    return RuleResult(
        rule_id="RULE-EXPIRY-CALC",
        rule_name="Sterile Shelf Life Expiry Arithmetic Consistency",
        version="v1.4.0",
        severity=RuleSeverity.CRITICAL,
        status="PASS",
        category=FindingCategory.EXPECTED_CHANGE,
        message=f"Expiry date '{expiry_date_str}' exactly matches MFG '{mfg_date_str}' + {shelf_life_months} months.",
        expected=expected_exp_str,
        actual=expiry_date_str,
        executed=True,
        test_ref="TC-EXP-01"
    )


def check_sterile_barrier_symbol(label_data: Dict[str, Any]) -> RuleResult:
    """
    RULE-STERILE-BARRIER: Validates presence of ISO 15223-1 sterile packaging symbol
    for primary sterile barrier packaging.
    """
    pkg_level = label_data.get("packaging_level", "")
    is_sterile = label_data.get("is_sterile", True)
    symbol = label_data.get("sterilization_symbol")
    
    # Applies to primary sterile packaging
    if pkg_level == "PRIMARY" and is_sterile:
        if not symbol or "STERILE" not in str(symbol).upper():
            return RuleResult(
                rule_id="RULE-STERILE-BARRIER",
                rule_name="ISO 15223-1 Sterile Barrier Identification",
                version="v3.0.0",
                severity=RuleSeverity.CRITICAL,
                status="FAIL",
                category=FindingCategory.CRITICAL_RULE_FAILURE,
                message="Primary sterile barrier packaging requires explicit ISO 15223-1 sterile symbol (e.g. 'STERILE EO').",
                expected="STERILE EO",
                actual="None / Missing",
                executed=True,
                test_ref="TC-STR-01"
            )
            
    return RuleResult(
        rule_id="RULE-STERILE-BARRIER",
        rule_name="ISO 15223-1 Sterile Barrier Identification",
        version="v3.0.0",
        severity=RuleSeverity.CRITICAL,
        status="PASS",
        category=FindingCategory.EXPECTED_CHANGE,
        message=f"Sterile barrier symbol verified: '{symbol}'.",
        expected="Valid Sterile Symbol",
        actual=str(symbol),
        executed=True,
        test_ref="TC-STR-01"
    )


def check_eco_propagation(
    label_data: Dict[str, Any],
    proposed_shelf_life_months: int,
    proposed_shelf_life_text: str
) -> RuleResult:
    """
    RULE-ECO-PROPAGATION: Verifies that the label incorporates the approved
    ECO proposed shelf life change (36 Months) rather than retaining legacy values (24 Months).
    """
    label_months = label_data.get("shelf_life_months")
    label_text = label_data.get("shelf_life_text", "")

    if label_months != proposed_shelf_life_months or proposed_shelf_life_text not in label_text:
        return RuleResult(
            rule_id="RULE-ECO-PROPAGATION",
            rule_name="ECO Attribute Change Propagation",
            version="v1.2.0",
            severity=RuleSeverity.CRITICAL,
            status="FAIL",
            category=FindingCategory.CRITICAL_RULE_FAILURE,
            message=(
                f"ECO change propagation failed: Expected shelf life '{proposed_shelf_life_text}' "
                f"({proposed_shelf_life_months} mo), but label contains '{label_text}' ({label_months} mo)."
            ),
            expected=f"{proposed_shelf_life_text} ({proposed_shelf_life_months} mo)",
            actual=f"{label_text} ({label_months} mo)",
            executed=True,
            test_ref="TC-PROP-01"
        )

    return RuleResult(
        rule_id="RULE-ECO-PROPAGATION",
        rule_name="ECO Attribute Change Propagation",
        version="v1.2.0",
        severity=RuleSeverity.CRITICAL,
        status="PASS",
        category=FindingCategory.EXPECTED_CHANGE,
        message=f"ECO shelf life '{proposed_shelf_life_text}' successfully propagated to candidate label.",
        expected=proposed_shelf_life_text,
        actual=label_text,
        executed=True,
        test_ref="TC-PROP-01"
    )


def execute_all_rules(
    label_data: Dict[str, Any],
    proposed_shelf_life_months: int = 36,
    proposed_shelf_life_text: str = "36 Months"
) -> List[RuleResult]:
    """Runs all implemented deterministic rules against the label candidate data."""
    results = [
        check_udi_syntax(label_data),
        check_expiry_calculation(label_data),
        check_sterile_barrier_symbol(label_data),
        check_eco_propagation(label_data, proposed_shelf_life_months, proposed_shelf_life_text)
    ]
    return results
