.PHONY: help test run dev docker build-frontend audit clean

help:
	@echo "OmniLabel AI - Enterprise Automation CLI"
	@echo "  make test           - Run full Pytest test suite (43 tests)"
	@echo "  make run            - Launch FastAPI backend on port 8000"
	@echo "  make dev            - Launch frontend development server (Vite)"
	@echo "  make docker         - Build and start full stack via Docker Compose"
	@echo "  make build-frontend - Compile production React static bundle"
	@echo "  make audit          - Verify SQLite SHA-256 audit ledger integrity"

test:
	pytest -v

run:
	uvicorn api:app --host 0.0.0.0 --port 8000 --reload

dev:
	cd frontend && npm run dev

docker:
	docker compose up --build -d

build-frontend:
	cd frontend && npm run build

audit:
	python -c "from src.audit import AuditLedger; ledger = AuditLedger(); res = ledger.verify_integrity(); print('Ledger Verified:', res)"
