"""Cryptographically hash-chained append-only SQLite audit ledger for OmniLabel AI."""

import sqlite3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from src.schemas import AuditEventRecord


class AuditLedger:
    """
    Maintains an append-only, SHA-256 hash-chained event ledger in SQLite.
    Provides complete reconstruction of change intake, discovery, verification,
    and review events.
    """

    GENESIS_HASH = "GENESIS_00000000000000000000000000000000"

    def __init__(self, db_path: str = "omnilabel_audit.db"):
        self.db_path = Path(db_path)
        self.init_db()

    def init_db(self):
        """Initializes SQLite schema for append-only audit trail."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    seq_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    artifact_refs_json TEXT NOT NULL,
                    prev_event_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_last_event_hash(self) -> str:
        """Retrieves the event_hash of the most recent recorded event."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_hash FROM audit_events ORDER BY seq_id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row[0]
            return self.GENESIS_HASH

    @staticmethod
    def compute_hash(
        prev_hash: str,
        event_id: str,
        timestamp: str,
        actor: str,
        role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details_str: str
    ) -> str:
        """Calculates SHA-256 hash across event payload and previous hash link."""
        payload = f"{prev_hash}|{event_id}|{timestamp}|{actor}|{role}|{action}|{entity_type}|{entity_id}|{details_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def append_event(
        self,
        event_id: str,
        actor: str,
        role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Dict[str, Any],
        artifact_refs: Optional[List[str]] = None
    ) -> AuditEventRecord:
        """Appends a new verified event to the ledger with hash chaining."""
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_hash = self.get_last_event_hash()
        
        details_json = json.dumps(details, sort_keys=True)
        artifact_refs_json = json.dumps(artifact_refs or [], sort_keys=True)

        event_hash = self.compute_hash(
            prev_hash=prev_hash,
            event_id=event_id,
            timestamp=timestamp,
            actor=actor,
            role=role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_str=details_json
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_events (
                    event_id, timestamp, actor, role, action, entity_type,
                    entity_id, details_json, artifact_refs_json, prev_event_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, timestamp, actor, role, action, entity_type,
                entity_id, details_json, artifact_refs_json, prev_hash, event_hash
            ))
            conn.commit()

        return AuditEventRecord(
            event_id=event_id,
            timestamp=timestamp,
            actor=actor,
            role=role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            artifact_refs=artifact_refs or [],
            prev_event_hash=prev_hash,
            event_hash=event_hash
        )

    def fetch_all_events(self) -> List[AuditEventRecord]:
        """Fetches all audit events in chronological sequence."""
        records: List[AuditEventRecord] = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT event_id, timestamp, actor, role, action, entity_type,
                       entity_id, details_json, artifact_refs_json, prev_event_hash, event_hash
                FROM audit_events ORDER BY seq_id ASC
            """)
            for row in cursor.fetchall():
                records.append(AuditEventRecord(
                    event_id=row[0],
                    timestamp=row[1],
                    actor=row[2],
                    role=row[3],
                    action=row[4],
                    entity_type=row[5],
                    entity_id=row[6],
                    details=json.loads(row[7]),
                    artifact_refs=json.loads(row[8]),
                    prev_event_hash=row[9],
                    event_hash=row[10]
                ))
        return records

    def verify_integrity(self) -> Tuple[bool, str]:
        """
        Walks the cryptographic hash chain from genesis to head,
        verifying that no historical records have been inserted, deleted, or altered.
        """
        events = self.fetch_all_events()
        if not events:
            return True, "Audit ledger is empty (clean state)"

        expected_prev_hash = self.GENESIS_HASH

        for idx, event in enumerate(events):
            # Check previous hash link
            if event.prev_event_hash != expected_prev_hash:
                return (
                    False,
                    f"Hash chain broken at sequence #{idx} (Event ID '{event.event_id}'): "
                    f"stored prev_hash '{event.prev_event_hash}' does not match expected '{expected_prev_hash}'"
                )

            # Recompute event hash
            recomputed = self.compute_hash(
                prev_hash=event.prev_event_hash,
                event_id=event.event_id,
                timestamp=event.timestamp,
                actor=event.actor,
                role=event.role,
                action=event.action,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                details_str=json.dumps(event.details, sort_keys=True)
            )

            if event.event_hash != recomputed:
                return (
                    False,
                    f"Cryptographic payload tampering detected at sequence #{idx} (Event ID '{event.event_id}'): "
                    f"stored hash '{event.event_hash}' != recomputed '{recomputed}'"
                )

            expected_prev_hash = event.event_hash

        return True, f"Cryptographic integrity verified across {len(events)} hash-chained events"

    def export_to_json(self, export_path: str):
        """Exports full audit history to a reviewable JSON file."""
        events = self.fetch_all_events()
        data = [e.model_dump() for e in events]
        Path(export_path).parent.mkdir(parents=True, exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
