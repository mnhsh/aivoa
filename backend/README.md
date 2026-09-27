# AIVOA Backend (FastAPI)

Modular backend for AIVOA with deterministic demo behavior, async DB support, AI workflow abstraction, and RAG fallback.

## Features

- **P0/P1 API surfaces**:
  - health checks: `/health`, `/health/live`, `/health/ready`
  - document upload with idempotent content hash
  - analyze via JSON and multipart upload
  - SSE analysis stream
  - deviations CRUD + detail/list/similar/evidence/fields/reassess
  - workflow trace inspection
  - knowledge docs listing + indexing
- **Safe DEMO_MODE**:
  - no Groq key/database required
  - deterministic extraction for AIVOA demo text
  - explicit `demo_mode` and `provider` in responses
- **Database strategy**:
  - PostgreSQL async URL supported
  - automatic SQLite fallback when `DATABASE_URL` is missing/unavailable
- **RAG strategy**:
  - in-memory retrieval fallback
  - pgvector-ready interface and stub adapter
- **AI workflow strategy**:
  - LangGraph integration when installed
  - robust sequential fallback when not installed

## Quickstart

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

API root: `http://localhost:8000/api/v1`

## Environment

- `DEMO_MODE=true` (default recommended for local deterministic behavior)
- `DATABASE_URL=` (optional; asyncpg URL for PostgreSQL, e.g. `postgresql+asyncpg://aivoa:aivoa@localhost:5432/aivoa`)
- `GROQ_API_KEY=` (optional; ignored for generation when DEMO_MODE is true)
- `GROQ_MODEL=llama-3.1-8b-instant`

## Migrations (Alembic)

```bash
alembic upgrade head
```

## Seed data

```bash
python -m app.seeds.seed_data
```

## Test

```bash
pytest -q
```
