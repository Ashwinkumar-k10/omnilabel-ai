"""Pydantic v2 data models for OmniLabel AI."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class FindingCategory(str, Enum):
    EXPECTED_CHANGE = "EXPECTED_CHANGE"
    CRITICAL_RULE_FAILURE = "CRITICAL_RULE_FAILURE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ScopeDisposition(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    AFFECTED = "AFFECTED"
    NOT_AFFECTED = "NOT_AFFECTED"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"


class ReleaseState(str, Enum):
    NOT_READY = "NOT_READY"
    SCOPE_BLOCKED = "SCOPE_BLOCKED"
    CHECKS_FAILED = "CHECKS_FAILED"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFORMATIONAL = "INFORMATIONAL"


class SourceSpan(BaseModel):
    field_name: str
    value: str
    doc_id: str
    doc_hash: str
    start_char: int
    end_char: int
    exact_text: str
    is_verified: bool = False
    verification_message: str = "Unverified"


class ExtractedECO(BaseModel):
    eco_id: str
    title: str
    product_family_id: str
    previous_shelf_life: str
    proposed_shelf_life: str
    proposed_shelf_life_months: int
    storage_condition: str
    effective_date: str
    target_markets: List[str]
    spans: Dict[str, SourceSpan] = Field(default_factory=dict)
    source_hash: str
    extraction_mode: str = "bounded_fixture"
    extractor_version: str = "v1.0.0"

    @field_validator("proposed_shelf_life_months")
    @classmethod
    def validate_positive_shelf_life(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Shelf life months must be positive")
        return v


class ProductFamily(BaseModel):
    family_id: str
    name: str
    device_class: str
    sterilization_type: str
    applicable_packaging_levels: List[str]


class CatalogVariant(BaseModel):
    variant_id: str
    name: str
    product_family_id: str
    sku_id: str
    packaging_level: str
    is_sterile: bool
    bears_expiry: bool
    market: str
    language: str
    current_shelf_life: Optional[str] = None
    current_shelf_life_months: Optional[int] = None
    storage_conditions: Optional[str] = None
    template_id: str
    baseline_artifact: str
    graph_connected: bool = True
    severed_edge_reason: Optional[str] = None
    udi_di: str
    status: str = "APPROVED_ACTIVE"


class TraversalPath(BaseModel):
    variant_id: str
    hops: List[str]
    explanation: str


class OrphanCandidate(BaseModel):
    variant_id: str
    name: str
    product_family_id: str
    sku_id: str
    packaging_level: str
    reason: str
    supporting_evidence: Dict[str, Any]
    disposition: ScopeDisposition = ScopeDisposition.UNRESOLVED
    reviewer_notes: Optional[str] = None
    disposition_timestamp: Optional[str] = None
    reviewer_role: Optional[str] = None


class ImpactInventory(BaseModel):
    eco_id: str
    forward_reachable_variants: List[str]
    orphan_candidates: List[OrphanCandidate]
    unaffected_variants: List[str]
    scope_complete: bool = False
    total_in_portfolio: int = 8
    summary: str = ""


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    version: str
    severity: RuleSeverity
    status: str  # PASS / FAIL / REVIEW_REQUIRED / NOT_RUN
    category: FindingCategory
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    executed: bool = True
    test_ref: Optional[str] = None


class VisualDiffFinding(BaseModel):
    finding_id: str
    category: FindingCategory
    description: str
    bounding_box: Dict[str, int]  # x, y, w, h
    severity: RuleSeverity
    is_benign: bool = False
    details: Optional[str] = None


class ReviewDecision(BaseModel):
    decision_id: str
    eco_id: str
    variant_id: str
    reviewer_name: str
    reviewer_role: str
    disposition: str  # APPROVED / REJECTED / NEEDS_REVISION
    rationale: str
    timestamp: str
    signature_ref: str
    conditions_met: bool = False


class AuditEventRecord(BaseModel):
    event_id: str
    timestamp: str
    actor: str
    role: str
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    artifact_refs: List[str] = Field(default_factory=list)
    prev_event_hash: str
    event_hash: str


class EvaluationMetrics(BaseModel):
    seeded_critical_defect_recall: float
    orphan_candidate_recall: float
    variant_discovery_recall: float
    extraction_exact_match_rate: float
    false_critical_rate: float
    audit_completeness: float
    denominators: Dict[str, str]
    software_version: str
    evaluation_timestamp: str
