"""Exact source-span provenance verification engine."""

import hashlib
from typing import Tuple
from src.schemas import SourceSpan


def compute_document_hash(text: str) -> str:
    """Compute SHA-256 hash of document text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_source_span(
    raw_text: str,
    start_char: int,
    end_char: int,
    expected_value: str
) -> Tuple[bool, str, str]:
    """
    Verify that raw_text[start_char:end_char] exactly matches expected_value
    under a strict, deterministic normalization policy.
    
    Returns:
        (is_verified: bool, actual_slice: str, message: str)
    """
    if start_char < 0 or end_char > len(raw_text) or start_char >= end_char:
        return (
            False,
            "",
            f"Invalid span bounds: [{start_char}:{end_char}] for text of length {len(raw_text)}"
        )
    
    actual_slice = raw_text[start_char:end_char]
    
    # Strict verbatim verification
    if actual_slice == expected_value:
        return True, actual_slice, "Exact verbatim span match verified"
    
    # Normalize internal single whitespace / stripped
    if actual_slice.strip() == expected_value.strip():
        return True, actual_slice, "Span matches expected value (normalized whitespace)"
        
    return (
        False,
        actual_slice,
        f"Span mismatch: expected '{expected_value}', extracted slice was '{actual_slice}'"
    )


def extract_and_verify_span(
    raw_text: str,
    field_name: str,
    target_substring: str,
    doc_id: str,
    doc_hash: str
) -> SourceSpan:
    """
    Locates target_substring within raw_text, computes exact start and end offsets,
    and runs deterministic provenance verification.
    """
    start_idx = raw_text.find(target_substring)
    if start_idx == -1:
        return SourceSpan(
            field_name=field_name,
            value=target_substring,
            doc_id=doc_id,
            doc_hash=doc_hash,
            start_char=-1,
            end_char=-1,
            exact_text="",
            is_verified=False,
            verification_message=f"Target value '{target_substring}' not found in source text"
        )
    
    end_idx = start_idx + len(target_substring)
    is_valid, actual_slice, msg = verify_source_span(raw_text, start_idx, end_idx, target_substring)
    
    return SourceSpan(
        field_name=field_name,
        value=target_substring,
        doc_id=doc_id,
        doc_hash=doc_hash,
        start_char=start_idx,
        end_char=end_idx,
        exact_text=actual_slice,
        is_verified=is_valid,
        verification_message=msg
    )
