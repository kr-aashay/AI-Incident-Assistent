# docs/decisions.md — Architecture & Engineering Decisions

## ADR 001: App Docker Build Context
- **Decision**: The application Docker image must always be built from the repository root using `docker build -f app/Dockerfile -t incident-assistant:latest .`.
- **Rationale**: The FastAPI application imports modules as `app.main`, `app.config`, etc. Setting the build context to the repo root ensures the full package hierarchy is preserved and consistent across local builds, CI/CD, and Docker Compose.

## ADR 002: Python Version and Dependency Resolution
- **Resolution Date**: 2026-10-04
- **Python Version**: Python 3.12.7 (Apple Silicon macOS / Darwin arm64)
- **Decision**: All dependencies are locked to exact versions resolved from active PyPI packages on Python 3.12.7. Runtime packages pinned: `fastapi==0.142.2` (web API), `uvicorn[standard]==0.54.0` (ASGI server), `pydantic==2.13.5` (validation), `pydantic-settings==2.15.0` (config), `sqlalchemy==2.1.3` (sync ORM & schema definition), `psycopg[binary]==3.3.6` (PostgreSQL driver), `httpx==0.28.1` (sync HTTP client), `anthropic==1.11.0` (Claude SDK), `prometheus-client==0.26.0` (metrics), `kubernetes==36.0.3` (K8s client). Dev packages pinned: `pytest==9.1.1`, `pytest-cov==7.1.0`, `respx==0.23.1`, `ruff==0.16.10`. Pre-commit hooks updated via `pre-commit autoupdate` (`ruff v0.16.10`, `pre-commit-hooks v6.0.0`, `gitleaks v8.30.0`).
