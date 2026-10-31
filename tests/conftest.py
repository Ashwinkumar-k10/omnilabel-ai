"""Pytest fixtures for OmniLabel AI testing."""

import json
from pathlib import Path
import pytest
from src.schemas import ExtractedECO
from src.extraction import extract_eco_data
from src.impact_graph import LabelDigitalThread
from src.orphan_scan import InverseCatalogScanner
from src.template_engine import ControlledTemplateEngine
from src.audit import AuditLedger


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def eco_demo_text(repo_root) -> str:
    path = repo_root / "data" / "eco_demo.txt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def eco_invalid_text(repo_root) -> str:
    path = repo_root / "data" / "eco_invalid.txt"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def extracted_eco(eco_demo_text) -> ExtractedECO:
    return extract_eco_data(eco_demo_text, doc_id="ECO-DEMO-001")


@pytest.fixture
def catalog_path(repo_root) -> str:
    return str(repo_root / "data" / "catalog.json")


@pytest.fixture
def ground_truth_path(repo_root) -> str:
    return str(repo_root / "data" / "ground_truth.json")


@pytest.fixture
def digital_thread(catalog_path) -> LabelDigitalThread:
    return LabelDigitalThread(catalog_path=catalog_path)


@pytest.fixture
def catalog_scanner(catalog_path) -> InverseCatalogScanner:
    return InverseCatalogScanner(catalog_path=catalog_path)


@pytest.fixture
def template_engine(repo_root) -> ControlledTemplateEngine:
    cand_data = repo_root / "data" / "templates"
    cand_root = repo_root / "templates"
    templates_dir = str(cand_data if cand_data.exists() else cand_root)
    return ControlledTemplateEngine(templates_dir=templates_dir)


@pytest.fixture
def baseline_variant_data(repo_root) -> dict:
    path = repo_root / "data" / "label_variants" / "LV-US-STER-001.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def test_audit_db(tmp_path) -> AuditLedger:
    db_file = tmp_path / "test_audit.db"
    return AuditLedger(db_path=str(db_file))
