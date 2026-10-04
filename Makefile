.PHONY: help venv lint test build compose-up compose-down \
        kind-up kind-load bootstrap demo-oom demo-crash \
        tf-validate kustomize-check clean

# Default target: print help.
help: ## Show this help message.
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile \
	  | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Development ───────────────────────────────────────────────────────────────

venv: ## Create .venv and install all dependencies.
	python3.12 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r app/requirements.txt -r app/requirements-dev.txt

lint: ## Run ruff linter and formatter check.
	.venv/bin/ruff check app/
	.venv/bin/ruff format --check app/

test: ## Run pytest with coverage.
	.venv/bin/pytest app/tests -v --cov=app --cov-report=term-missing

# ── Docker ────────────────────────────────────────────────────────────────────
# NOTE (Phase 4): build uses repo root as context so app/ code is accessible.
# Command will be: docker build -f app/Dockerfile -t incident-assistant:dev .

build: ## Build both Docker images (app and demo-app).
	@echo "Implemented in Phase 4 — run that phase first."

compose-up: ## Start the local docker compose stack.
	@echo "Implemented in Phase 4 — run that phase first."

compose-down: ## Stop the local docker compose stack.
	@echo "Implemented in Phase 4 — run that phase first."

# ── Kubernetes (kind) ─────────────────────────────────────────────────────────

kind-up: ## Create the kind cluster (scripts/kind-up.sh).
	@echo "Implemented in Phase 5 — run that phase first."

kind-load: ## Load Docker images into the kind cluster.
	@echo "Implemented in Phase 5 — run that phase first."

bootstrap: ## Deploy app stack onto the kind cluster (scripts/bootstrap.sh).
	@echo "Implemented in Phase 5 — run that phase first."

# ── Demo triggers ─────────────────────────────────────────────────────────────

demo-oom: ## Trigger an OOMKilled event in the demo-app.
	@echo "Implemented in Phase 6 — run that phase first."

demo-crash: ## Trigger a CrashLoopBackOff in the demo-app.
	@echo "Implemented in Phase 6 — run that phase first."

# ── Infrastructure ────────────────────────────────────────────────────────────

tf-validate: ## Run terraform fmt -check and terraform validate.
	@echo "Implemented in Phase 8 — run that phase first."

kustomize-check: ## kustomize build both overlays and validate with kubeconform.
	@echo "Implemented in Phase 5 — run that phase first."

# ── Housekeeping ──────────────────────────────────────────────────────────────

clean: ## Remove Python cache, pytest cache, and coverage artifacts.
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f .coverage
	rm -rf htmlcov/
