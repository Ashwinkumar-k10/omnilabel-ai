"""Automated tests for SQLite append-only audit trail and SHA-256 hash chaining."""

import sqlite3
from src.audit import AuditLedger


def test_audit_event_logging_and_hash_chaining(test_audit_db):
    # Log 3 events
    e1 = test_audit_db.append_event(
        event_id="EVT-001",
        actor="System",
        role="Ingestion Engine",
        action="ECO_INTAKE",
        entity_type="ECO",
        entity_id="ECO-DEMO-001",
        details={"source": "eco_demo.txt"}
    )
    assert e1.prev_event_hash == AuditLedger.GENESIS_HASH

    e2 = test_audit_db.append_event(
        event_id="EVT-002",
        actor="Dr. Vance",
        role="Packaging Engineer",
        action="ORPHAN_SURFACED",
        entity_type="LABEL_VARIANT",
        entity_id="LV-ORPHAN-001",
        details={"reason": "candidate_match_but_no_graph_path"}
    )
    assert e2.prev_event_hash == e1.event_hash

    e3 = test_audit_db.append_event(
        event_id="EVT-003",
        actor="Dr. Chen",
        role="QA Director",
        action="HUMAN_APPROVAL",
        entity_type="LABEL_VARIANT",
        entity_id="LV-US-STER-001",
        details={"disposition": "APPROVED"}
    )
    assert e3.prev_event_hash == e2.event_hash

    # Verify integrity passes
    is_valid, msg = test_audit_db.verify_integrity()
    assert is_valid is True
    assert "Cryptographic integrity verified across 3" in msg


def test_audit_tamper_detection(test_audit_db):
    """
    CRITICAL ACCEPTANCE TEST:
    Modifying any historical record in the SQLite database breaks the cryptographic
    hash chain and is immediately flagged by verify_integrity().
    """
    test_audit_db.append_event(
        event_id="EVT-101",
        actor="System",
        role="Ingestion Engine",
        action="ECO_INTAKE",
        entity_type="ECO",
        entity_id="ECO-DEMO-001",
        details={"status": "initial"}
    )
    test_audit_db.append_event(
        event_id="EVT-102",
        actor="Auditor",
        role="Reviewer",
        action="VERIFICATION_PASS",
        entity_type="RULE",
        entity_id="RULE-UDI",
        details={"checks": "ok"}
    )

    # Tamper with row 1 details directly via SQLite
    with sqlite3.connect(test_audit_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE audit_events SET details_json = '{\"tampered\": true}' WHERE event_id = 'EVT-101'")
        conn.commit()

    is_valid, msg = test_audit_db.verify_integrity()
    assert is_valid is False
    assert "Cryptographic payload tampering detected" in msg or "Hash chain broken" in msg


def test_export_audit_json(test_audit_db, tmp_path):
    test_audit_db.append_event(
        event_id="EVT-EXPORT-1",
        actor="System",
        role="Engine",
        action="TEST_ACTION",
        entity_type="TEST",
        entity_id="ID-1",
        details={"data": 123}
    )
    out_file = tmp_path / "export.json"
    test_audit_db.export_to_json(str(out_file))
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "EVT-EXPORT-1" in content
