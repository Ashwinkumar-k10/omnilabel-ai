# OmniLabel AI
### Enterprise Medical Device Label Change Intelligence Platform

[![CI/CD Pipeline](https://github.com/Ashwinkumar-k10/omnilabel-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashwinkumar-k10/omnilabel-ai/actions)
[![Release](https://img.shields.io/badge/Release-v1.0.0-blue?style=flat-square&logo=github)](https://github.com/Ashwinkumar-k10/omnilabel-ai/releases)
[![Automated Tests](https://img.shields.io/badge/Pytest-43%20Passed%20%7C%200%20Failed-10b981?style=flat-square&logo=pytest&logoColor=white)](https://github.com/Ashwinkumar-k10/omnilabel-ai/actions)
[![Audit Integrity](https://img.shields.io/badge/Audit%20Ledger-SHA--256%20Hash%20Chained-0f766e?style=flat-square)](https://github.com/Ashwinkumar-k10/omnilabel-ai)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Tailwind%20CSS-2563eb?style=flat-square&logo=react&logoColor=white)](https://github.com/Ashwinkumar-k10/omnilabel-ai)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-059669?style=flat-square&logo=fastapi&logoColor=white)](https://github.com/Ashwinkumar-k10/omnilabel-ai)
[![Compliance Standard](https://img.shields.io/badge/Standard-FDA%2021%20CFR%20Part%2011%20%7C%20EU%20MDR-1e293b?style=flat-square)](https://github.com/Ashwinkumar-k10/omnilabel-ai)

> **Core Operating Principle:**  
> *Probabilistic AI Extracts • Deterministic Rules Decide • Qualified Humans Sign*
>
> **Core Differentiator:**  
> *Find the label your change could miss.*

---

## 1. Executive Summary

In medical device manufacturing, engineering and regulatory changes (e.g., extending qualified sterile shelf life from 24 months to 36 months) propagate across complex multi-tier hierarchies: **Product Families &rarr; SKUs &rarr; Packaging Tiers &rarr; Market-Specific Label Variants**.

A critical vulnerability in life-sciences change control is **silent scope omission**: when legacy ERP/PLM catalog relationships are severed or missing, standard graph traversal silently overlooks disconnected label variants. Unreviewed labels bypass quality gates, creating severe regulatory non-compliance under FDA 21 CFR Part 820 and EU MDR 2017/745.

**OmniLabel AI** is an enterprise-grade change-intelligence platform designed to eliminate scope omission through **Uncertainty-Aware Dual Discovery**:
1. **Forward Digital Thread Traversal:** Rapidly tracks all explicitly linked variants across the product tree.
2. **Independent Inverse Catalog Scanning:** Concurrently evaluates independent catalog attributes (sterility status, product family codes, packaging tiers, expiry requirements) to surface orphaned candidates whose relational edges are broken.
3. **Safe Scope Gate:** Enforces an unbypassable regulatory hold that prevents release approval until all uncertain candidates are triaged by a qualified human reviewer.
4. **Controlled Template Drafting:** Restricts artwork updates to validated SVG template injection (Jinja2) to eliminate generative AI hallucinations in regulated packaging.
5. **Deterministic Verification & Computer Vision:** Enforces exact GS1 GTIN-14 Mod-10 check digit mathematics, ISO 15223-1 medical symbol adherence, expiry arithmetic, and OpenCV pixel-difference analysis.
6. **21 CFR Part 11 Electronic Signature & Tamper-Evident Ledger:** Every event is recorded in an append-only cryptographic ledger with forward SHA-256 hash chaining.

---

## 2. System Architecture

OmniLabel AI uses a decoupled enterprise architecture comprising a high-performance **FastAPI** backend runtime, a modern **React 18** clinical SaaS dashboard, and a **Dockerized** CI/CD deployment pipeline.

```
                              ┌──────────────────────────────────────────────┐
                              │    Engineering Change Order (ECO Document)   │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
                              ┌──────────────────────────────────────────────┐
                              │      Bounded Character-Span Extractor        │
                              │    (Exact Substring & SHA-256 Provenance)    │
                              └──────────────────────┬───────────────────────┘
                                                     │
                       ┌─────────────────────────────┴─────────────────────────────┐
                       │                                                           │
                       ▼                                                           ▼
       ┌───────────────────────────────┐                           ┌───────────────────────────────┐
       │   Forward Digital Thread      │                           │  Independent Inverse Catalog  │
       │   Graph Traversal (NetworkX)  │                           │   Scanner (Attribute Match)   │
       └───────────────┬───────────────┘                           └───────────────┬───────────────┘
                       │                                                           │
                       │   [Known Hierarchy Links]                                 │   [Orphaned Candidate]
                       ▼                                                           ▼
       ┌───────────────────────────────┐                           ┌───────────────────────────────┐
       │  4 Forward-Linked Variants    │                           │  1 Orphaned Variant Detected  │
       └───────────────┬───────────────┘                           └───────────────┬───────────────┘
                       │                                                           │
                       └─────────────────────────────┬─────────────────────────────┘
                                                     │
                                                     ▼
                                      ┌─────────────────────────────┐
                                      │    SAFE REGULATORY GATE     │
                                      │  (Blocks Release Approval   │
                                      │   Until Triage is Complete) │
                                      └──────────────┬──────────────┘
                                                     │ Human QA Triage
                                                     ▼
                                      ┌─────────────────────────────┐
                                      │ Controlled SVG Drafting     │
                                      │ (Jinja2 + PyMuPDF Engine)   │
                                      └──────────────┬──────────────┘
                                                     │
                                                     ▼
                                      ┌─────────────────────────────┐
                                      │ Deterministic Rules & CV    │
                                      │ • GS1 GTIN-14 Mod-10 Check  │
                                      │ • ISO 15223-1 Sterile Symbol│
                                      │ • OpenCV Pixel Diff Heatmap │
                                      └──────────────┬──────────────┘
                                                     │
                                                     ▼
                                      ┌─────────────────────────────┐
                                      │ 21 CFR Part 11 E-Signature  │
                                      │ & SHA-256 Chained Ledger    │
                                      └─────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Component | Technology | Description |
|:---|:---|:---|:---|
| **Frontend** | Clinical UI | React 18, Tailwind CSS, Lucide | Enterprise life-sciences SaaS interface with Linear/Veeva-inspired design tokens |
| **API Gateway** | REST Services | FastAPI, Uvicorn, Pydantic v2 | High-throughput asynchronous endpoints with OpenAPI 3.1 specification |
| **Graph Intelligence** | Digital Thread | NetworkX | Multi-level directed graph modeling ECOs, product families, packaging tiers, and label variants |
| **Inverse Discovery** | Orphan Scanner | Python Core Engine | Deterministic set intersection and attribute filter isolating disconnected variants |
| **Artwork Engine** | Template Generator | Jinja2, PyMuPDF (fitz) | Parameterized SVG template rendering and high-resolution rasterization (PNG/PDF) |
| **Visual QA** | Difference Engine | OpenCV (cv2), NumPy | Pixel-level delta calculation, bounding-box localization, and 3-way triage classification |
| **Compliance Ledger** | Cryptographic Audit | SQLite, `hashlib` (SHA-256) | Append-only tamper-evident ledger linking sequential events via cryptographic hashes |
| **DevOps & CI/CD** | Pipeline & Containers | Docker, GitHub Actions | Multi-stage container builds and automated continuous verification workflows |

---

## 4. Repository Structure

```text
omnilabel-ai/
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI/CD (Pytest suite + React build)
├── .gitignore                         # Excludes node_modules, *.db, __pycache__, .pytest_cache
├── Dockerfile                         # Production multi-stage build (Node 22 + Python 3.11)
├── docker-compose.yml                 # Full-stack container orchestration
├── README.md                          # Platform documentation & architecture reference
├── requirements.txt                   # Production Python backend dependencies
├── api.py                             # FastAPI REST service & React frontend static mount
│
├── data/
│   ├── catalog.json                   # Product catalog (SKUs, packaging hierarchy, GTIN prefixes)
│   ├── eco_demo.txt                   # Baseline Engineering Change Order (ECO-2024-0891)
│   ├── eco_invalid.txt                # Invalid ECO test fixture (tampered GTIN / format breach)
│   ├── ground_truth.json              # Pre-frozen ground-truth acceptance manifest
│   └── label_variants/                # 8 Synthetic production labeling variants
│       ├── LV-EU-CART-001.json
│       ├── LV-EU-IFU-001.json
│       ├── LV-EU-STER-001.json
│       ├── LV-ORPHAN-001.json         # Disconnected variant surfaced by inverse scan
│       ├── LV-US-CART-001.json
│       ├── LV-US-IFU-001.json
│       ├── LV-US-SHIP-001.json
│       └── LV-US-STER-001.json
│
├── evidence/                          # Pre-computed compliance evidence & audit exports
│   ├── 02_test_manifest.json          # Deterministic test harness metadata
│   ├── 03_test_results.json           # Pytest validation execution logs
│   ├── 04_orphan_scan_report.json     # Independent inverse catalog recovery logs
│   ├── 07_audit_event_export.json     # 21 CFR Part 11 append-only cryptographic log
│   └── test_run_report.json           # Evaluation metrics (100% recall, 0 regressions)
│
├── frontend/                          # Enterprise React SaaS Dashboard (Linear/Veeva style)
│   ├── index.html                     # HTML5 entry with Inter font
│   ├── package.json                   # React 18, Tailwind CSS, Lucide icons, Vite
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── tailwind.config.js             # Enterprise color tokens (#0B1220 Midnight, #0F766E Clinical Teal)
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx                    # 5-stage workflow UI + SVG digital thread graph
│       ├── index.css                  # Global styles, scrollbars, and keyframes
│       └── main.jsx                   # React root mount
│
├── src/                               # Modular Python Verification & AI Pipeline
│   ├── __init__.py
│   ├── schemas.py                     # Strict Pydantic v2 data models
│   ├── extraction.py                  # Character-offset bounded change extraction
│   ├── provenance.py                  # Verbatim substring verification & SHA-256 doc hashing
│   ├── impact_graph.py                # NetworkX digital thread forward traversal
│   ├── orphan_scan.py                 # Independent catalog inverse scan (Core Differentiator)
│   ├── template_engine.py             # Jinja2 SVG generator & PyMuPDF rasterizer
│   ├── rules.py                       # GS1 Mod-10, ISO 15223-1, Expiry arithmetic
│   ├── visual_diff.py                 # OpenCV pixel-level diff & 3-way triage classifier
│   ├── review.py                      # 21 CFR Part 11 electronic signature authorization gate
│   ├── audit.py                       # SQLite append-only SHA-256 hash-chained ledger
│   └── report.py                      # Ground-truth evaluation metrics engine
│
├── templates/
│   ├── approved_label.svg             # Baseline approved SVG template (ISO 15223-1 symbols)
│   └── approved_label_benign.svg      # Benign visual shift test template
│
└── tests/                             # Automated Test Harness (43 Passed, 100% Green)
    ├── __init__.py
    ├── conftest.py
    ├── test_api.py                    # REST API endpoint tests
    ├── test_audit.py                  # SHA-256 chain verification & tamper detection tests
    ├── test_end_to_end.py             # Full ECO intake-to-ledger integration tests
    ├── test_impact_graph.py           # Forward graph traversal tests
    ├── test_orphan_scan.py            # Disconnected variant recovery tests
    ├── test_provenance.py             # Exact offset verification tests
    ├── test_report.py                 # Precision / recall metrics tests
    ├── test_review.py                 # Sign-off authorization state gate tests
    ├── test_rules.py                  # GS1 check-digit & regulatory rule tests
    ├── test_template_engine.py        # SVG drafting & PyMuPDF rasterizer tests
    └── test_visual_diff.py            # OpenCV pixel diff & classification tests
```

---

## 5. Verified Ground-Truth Metrics

Evaluated against the pre-frozen regulatory ground-truth acceptance manifest ([`data/ground_truth.json`](data/ground_truth.json)):

| Regulatory Validation Metric | Requirement | Measured Result | Benchmark | Status |
|:---|:---:|:---:|:---:|:---:|
| **Orphan-Candidate Recall** | 100.0% | **100.0%** | 1 / 1 disconnected variant surfaced | **PASSED** |
| **Total Variant Discovery Recall** | 100.0% | **100.0%** | 5 / 5 affected variants captured | **PASSED** |
| **Critical Defect Detection Recall** | 100.0% | **100.0%** | 4 / 4 seeded defects blocked | **PASSED** |
| **Source Provenance Exact-Match** | 100.0% | **100.0%** | 5 / 5 character-spans verified | **PASSED** |
| **False-Critical Alarm Rate** | 0.0% | **0.0%** | 0 / 2 benign shifts flagged critical | **PASSED** |
| **Cryptographic Audit Completeness** | 100.0% | **100.0%** | All state changes hash-chained | **PASSED** |
| **Automated Test Suite Pass Rate** | 100.0% | **100.0%** | 43 / 43 Pytest test cases passing | **PASSED** |

---

## 6. Quick Start & Execution

### Prerequisites
* Python 3.11+
* Node.js 20+ (for local frontend development)
* Docker & Docker Compose (optional for containerized deployment)

---

### Option A: Local Development Setup

#### 1. Clone Repository & Setup Python Environment
```bash
git clone https://github.com/Ashwinkumar-k10/omnilabel-ai.git
cd omnilabel-ai

python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. Execute Automated Verification Suite
Run the full 43-test suite including cryptographic tamper verification:
```bash
pytest -v
```

#### 3. Build React Frontend & Launch FastAPI Service
```bash
# Build production React web bundle
cd frontend
npm install
npm run build
cd ..

# Launch production API service
uvicorn api:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** in any web browser to interact with the platform.

---

### Option B: One-Command Docker Deployment

Deploy the entire full-stack application inside a single containerized environment:

```bash
docker compose up --build -d
```
The application will be compiled and available at **`http://localhost:8000`**.

---

## 7. API Reference (FastAPI)

The FastAPI server provides an interactive OpenAPI / Swagger UI at **`http://localhost:8000/docs`**.

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/status` | `GET` | Current system state (scope status, rule checks, blockers, hash chain status) |
| `/api/eco` | `GET` | Verified character-span offsets and document hash for active ECO |
| `/api/inventory` | `GET` | Digital thread variants, graph traversal status, and orphan findings |
| `/api/orphan/triage` | `POST` | Regulatory triage submission (`AFFECTED` or `NOT_AFFECTED`) to clear the Scope Gate |
| `/api/candidate` | `GET` | Controlled SVG label revision, visual diff metrics, and baseline comparisons |
| `/api/candidate/pdf` | `GET` | High-resolution PDF export of the generated label |
| `/api/verify` | `POST` | Deterministic validation engine check (GTIN Mod-10, symbols, dates) |
| `/api/review/sign` | `POST` | 21 CFR Part 11 electronic signature authorization gate |
| `/api/audit` | `GET` | Cryptographic ledger event stream and SHA-256 chain verification status |
| `/api/metrics` | `GET` | Live recall, precision, and defect detection metrics vs. ground truth |

---

## 8. Continuous Integration & Quality Assurance

The repository includes a production **GitHub Actions CI/CD Pipeline** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) running on every push and pull request to `main`:

* **Job 1: Backend Verification & Cryptographic Ledger Integrity:**
  * Runs on `ubuntu-latest` with Python 3.11.
  * Executes the complete **43 Pytest suite** covering graph traversal, inverse scanning, rules, visual diffs, and API endpoints.
  * Dynamically tests SQLite append-only SHA-256 hash chaining and tamper-detection invariants.
  * Archives regulatory compliance evidence packages.
* **Job 2: React Frontend Build & Asset Verification:**
  * Runs on `ubuntu-latest` with Node.js 22.
  * Installs dependencies and runs Vite production compilation.
  * Validates CSS tokens, layout components, and bundle packaging.

---

## 9. Regulatory Disclaimer

OmniLabel AI is a software prototype developed for **Tata Elxsi TELEPORT Season 4 (Case Study 4: Healthcare & Life Sciences)**. It demonstrates human-supervised change control, dual-path impact discovery, and deterministic rule validation. It is designed to assist and augment qualified regulatory affairs and quality assurance personnel, not to serve as an unvalidated autonomous medical-device release authority.

---

## 10. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
