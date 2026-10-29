"""Automated tests for FastAPI enterprise endpoints."""

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "OPERATIONAL"


def test_api_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "scope_complete" in data
    assert "audit_chain_valid" in data
    assert data["audit_chain_valid"] is True


def test_api_eco():
    res = client.get("/api/eco")
    assert res.status_code == 200
    data = res.json()
    assert data["eco_id"] == "ECO-DEMO-001"
    assert "spans" in data
    assert len(data["spans"]) >= 5


def test_api_inventory():
    res = client.get("/api/inventory")
    assert res.status_code == 200
    data = res.json()
    assert len(data["forward_reachable"]) == 4
    assert len(data["orphan_candidates"]) == 1
    assert data["orphan_candidates"][0]["variant_id"] == "LV-ORPHAN-001"


def test_api_candidate():
    res = client.get("/api/candidate")
    assert res.status_code == 200
    data = res.json()
    assert "baseline_png_base64" in data
    assert "candidate_png_base64" in data
    assert "candidate_svg" in data


def test_api_verify():
    res = client.get("/api/verify")
    assert res.status_code == 200
    data = res.json()
    assert "rule_results" in data
    assert "diff_findings" in data
    assert "diff_heatmap_base64" in data


def test_api_audit():
    res = client.get("/api/audit")
    assert res.status_code == 200
    data = res.json()
    assert data["is_intact"] is True
    assert len(data["events"]) >= 1


def test_api_metrics():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["orphan_candidate_recall"] == 1.0
    assert data["variant_discovery_recall"] == 1.0
