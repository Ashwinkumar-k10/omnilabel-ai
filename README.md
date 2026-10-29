# OmniLabel AI
## Evidence-Driven Medical Device Label Change Intelligence Platform

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions%20Active-brightgreen?style=flat-square&logo=githubactions)](https://github.com)
[![Automated Tests](https://img.shields.io/badge/Pytest-44%20Passed%20%7C%200%20Failed-success?style=flat-square&logo=pytest)](https://github.com)
[![Audit Integrity](https://img.shields.io/badge/Audit%20Ledger-SHA--256%20Hash%20Chained-teal?style=flat-square)](https://github.com)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Tailwind-blue?style=flat-square&logo=react)](https://github.com)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-emerald?style=flat-square&logo=fastapi)](https://github.com)
[![Regulatory](https://img.shields.io/badge/Standard-FDA%2021%20CFR%20820%20%7C%20EU%20MDR-darkblue?style=flat-square)](https://github.com)

**Competition:** Tata Elxsi TELEPORT Season 4 — Case Study 4: Healthcare & Life Sciences  
**Tagline:** *Find the label your change could miss.*  
**Operating Principle:** *Probabilistic AI Extracts • Deterministic Rules Decide • Qualified Humans Sign.*

---

## 1. Executive Summary & Purpose

Medical device labeling changes (e.g. extending qualified sterile shelf life from 24 months to 36 months) propagate across complex product families, SKUs, and packaging tiers. 

When product-to-label catalog links are missing or corrupted during PLM/ERP database migrations, conventional graph-traversal systems experience **silent scope omission**: an affected label is bypassed and never enters regulatory review.

**OmniLabel AI** solves this through **Uncertainty-Aware Impact Discovery**:
1. **Forward Graph Traversal:** Identifies variants linked via explicit digital thread relationships in NetworkX.
2. **Independent Inverse Catalog Scan:** Concurrently evaluates independent catalog metadata against ECO change criteria (product family, sterility status, packaging tiers, expiry requirements) to surface orphaned candidates whose graph relationships are severed.
3. **Safe Scope Gate:** Blocks workflow completion and release approval while any candidate in the **Scope-Uncertainty Queue** remains unresolved.
4. **Controlled Template Drafting:** Revision values are populated into approved SVG templates using Jinja2 without unconstrained AI hallucination.
5. **Deterministic Rules & OpenCV Diff:** Checks GS1 GTIN-14 check digits, expiry arithmetic, ISO 15223-1 symbols, and visual pixel differences with 3-way triage (`EXPECTED_CHANGE`, `CRITICAL_RULE_FAILURE`, `REVIEW_REQUIRED`).
6. **Immutable Cryptographic Audit Trail:** Every intake, discovery, draft, check, and human approval event is recorded in SQLite with SHA-256 cryptographic hash-chaining.
7. **Production Decoupled Architecture:** High-performance **FastAPI** backend + **React 18** industrial SaaS dashboard with automated **GitHub Actions CI/CD**.

---

## 2. Architecture & Tech Stack

```text
                        ┌──────────────────────────────────────────────┐
                        │              git push origin main            │
                        └──────────────────────┬───────────────────────┘
                                               │
                                               ▼
         ┌────────────────────────────────────────────────────────────────────────────┐
         │                  GITHUB ACTIONS CI/CD WORKFLOW MATRIX                      │
         ├─────────────────────────────────────┬──────────────────────────────────────┤
         │  Job 1: Python Backend Test Suite   │  Job 2: React Frontend Build         │
         │  • Sets up Python 3.11              │  • Sets up Node.js 22                │
         │  • Runs 44 Pytest Acceptance Tests  │  • Installs npm packages             │
         │  • Verifies SHA-256 Hash Chaining   │  • Type-checks & builds production   │
         │  • Validates Ground-Truth Manifest  │    optimized web bundle              │
         ├─────────────────────────────────────┴──────────────────────────────────────┤
         │  Job 3: Automated Deployment Gate                                          │
         │  • If all 44 tests PASS ──► Production Docker & Web Deployment             │
         └────────────────────────────────────────────────────────────────────────────┘
```

| Layer | Technology | Role |
|---|---|---|
| **Frontend UI** | React 18, Tailwind CSS, Lucide Icons, Vite | Industrial MedTech Regulatory Dashboard |
| **API Layer** | FastAPI, Uvicorn, Pydantic v2 | High-performance REST endpoints |
| **Digital Thread** | NetworkX | Product family, SKU & label graph traversal |
| **Template Engine** | SVG + Jinja2 + PyMuPDF | Controlled drafting & high-res rasterization |
| **Verification** | OpenCV + Python Deterministic Rules | Pixel difference analysis & GS1 checksums |
| **Audit Ledger** | SQLite + SHA-256 Hash Chaining | Append-only cryptographically linked event log |
| **CI/CD** | GitHub Actions | Automated regression tests & production builds |
| **Containerization** | Docker, Docker Compose | Reproducible one-command deployment |

---

## 3. Repository Structure

```text
a:\Projects\Tata_elexsi\
├── .github/workflows/ci.yml              # GitHub Actions CI/CD pipeline (tests + build)
├── Dockerfile                            # Multi-stage production container build
├── docker-compose.yml                    # One-command full-stack container deployment
├── api.py                                # FastAPI enterprise REST service & React frontend mount
├── requirements.txt                      # Backend dependencies
├── .gitignore                            # Clean repository exclusions
├── README.md                             # Comprehensive documentation
├── data/
│   ├── eco_demo.txt                      # Synthetic ECO-DEMO-001 source document
│   ├── catalog.json                      # Independent master catalog (8 portfolio variants)
│   ├── ground_truth.json                 # Pre-frozen ground-truth acceptance manifest
│   └── label_variants/                   # Baseline variant definitions
├── templates/
│   ├── approved_label.svg                # Controlled Jinja2 SVG label template
│   └── approved_label_benign.svg         # SVG template with harmless 5px logo displacement
├── src/
│   ├── schemas.py                        # Pydantic v2 data models
│   ├── extraction.py                     # Bounded attribute extractor
│   ├── provenance.py                     # Exact character-span provenance verifier
│   ├── impact_graph.py                   # NetworkX digital thread & forward traversal
│   ├── orphan_scan.py                    # Inverse catalog scanner & safe scope gate
│   ├── template_engine.py                # Jinja2 SVG rendering engine & PyMuPDF rasterizer
│   ├── rules.py                          # Deterministic GS1, expiry & ISO rules
│   ├── visual_diff.py                    # OpenCV pixel difference analysis & triage
│   ├── review.py                         # Quality & regulatory release gating workflow
│   ├── audit.py                          # SQLite SHA-256 hash-chained immutable audit ledger
│   └── report.py                         # Ground-truth metric evaluator & evidence exporter
├── frontend/                             # Enterprise React 18 + Tailwind SaaS Frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── App.jsx                       # Master 5-stage interactive dashboard
│   │   ├── index.css
│   │   └── main.jsx
│   └── dist/                             # Compiled production web bundle
├── tests/
│   ├── test_api.py                       # FastAPI endpoint test suite
│   ├── test_provenance.py                # Exact character-span provenance tests
│   ├── test_impact_graph.py              # Forward graph traversal tests
│   ├── test_orphan_scan.py               # Inverse catalog scan & scope gate tests
│   ├── test_template_engine.py           # Controlled drafting tests
│   ├── test_rules.py                     # Deterministic rule checks & defect tests
│   ├── test_visual_diff.py               # Visual diffing tests
│   ├── test_review.py                    # Human review gating tests
│   ├── test_audit.py                     # Cryptographic hash-chaining tests
│   ├── test_report.py                    # Ground-truth metrics tests
│   └── test_end_to_end.py                # Full integration test
└── evidence/                             # Exported test results & audit packages
```

---

## 4. Run Instructions

### A. Run Automated Test Suite (44/44 Tests)
```bash
pytest -v
```

### B. Launch Enterprise Web Platform (React + FastAPI)
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** in any browser.

---

## 5. Measured Test Results & Ground-Truth Verification

Evaluated against the pre-frozen ground-truth acceptance manifest (`data/ground_truth.json`):

| Metric | Target | Actual Measured Result | Denominator | Outcome |
|---|---|---|---|---|
| **Orphan-Candidate Recall** | 100% | **100%** | 1 / 1 orphan surfaced | **PASS** |
| **Variant Discovery Recall** | 100% | **100%** | 5 / 5 affected variants found | **PASS** |
| **Seeded Critical-Defect Recall** | 100% | **100%** | 4 / 4 defects detected | **PASS** |
| **Extraction Exact-Match Rate** | 100% | **100%** | 5 / 5 fields verified with exact spans | **PASS** |
| **False-Critical Rate** | 0.0% | **0.0%** | 0 / 2 benign shifts marked critical | **PASS** |
| **Audit Completeness** | 100% | **100%** | All workflow events verified | **PASS** |
| **Automated Test Suite** | 100% | **100%** | 44 / 44 pytest test cases passing | **PASS** |

---

## 6. How to Demonstrate to the Judges (90-Second Script)

1. **0–10s: Frame the Problem**  
   Open `http://localhost:8000`. Show the executive header and explain: *"A medical device change affects multiple packaging tiers. The catastrophic failure is not a typo—it is an affected label never entering review because its catalog link was severed."*
2. **10–30s: Show the Differentiator (Stage 2)**  
   Switch to **Tab 2 (Dual Discovery & Thread)**. Show the SVG topology diagram:
   - Forward traversal missed `LV-ORPHAN-001` (red severed link).
   - The **Inverse Catalog Scan** (amber radar beam) detected it independently from metadata.
   - The **Scope Gate** is actively engaged, blocking release.
3. **30–45s: Resolve the Scope Gate**  
   Click **"Open Regulatory Triage Drawer"**, set disposition to `AFFECTED`, and submit. The top status bar instantly updates to `● SCOPE RESOLVED (5/5 Variants)`.
4. **45–65s: Show Controlled Revision & Defensive QA (Stages 3 & 4)**  
   Show the controlled SVG candidate with updated 36-month shelf life. In the sidebar, select **"DEFECT 1: Expiry Arithmetic Error"**. Tab 4 immediately flags `RULE-EXPIRY-CALC` as `CRITICAL_RULE_FAILURE`, and release authorization is blocked.
5. **65–80s: Execute 21 CFR Part 11 Sign-off & Audit (Stage 5)**  
   Reset to clean draft, switch to Tab 5, sign as QA Director, and show the live **SHA-256 Hash Chain Integrity** verification.
6. **80–90s: Highlight Engineering Maturity**  
   Point to the **GitHub Actions CI/CD pipeline** and 44 passing automated unit and integration tests.
