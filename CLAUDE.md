# CLAUDE.md

## Running the project

```bash
# Build and run everything (recommended)
docker compose up --build

# Dev: backend only (requires backend/.env with OPENAI_API_KEY)
cd backend && uv sync && uv run uvicorn main:app --reload --port 8000

# Dev: frontend only
cd frontend && npm install && npm run dev

# Lint frontend
cd frontend && npm run lint

# Run tests
cd backend && uv run pytest
```

## Architecture

Two-stage Docker build: Node 22 builds the Next.js frontend as static files (`next build` with `output: 'export'`), then Python 3.12 serves them alongside the FastAPI backend via `StaticFiles`.

**Request flow:**
1. Browser hits `GET /` — served as static HTML from `/app/backend/static/` (compiled Next.js `out/`)
2. Browser calls `POST /ingest` (upload PDF) or `POST /query` (ask a question) — handled by FastAPI
3. `main.py` delegates to `rag.py`, which uses **LangChain + LangGraph** to embed the PDF into ChromaDB and query via `gpt-4o-mini`

**Key files:**
- `backend/main.py` — FastAPI app: `/ingest` and `/query` endpoints, duplicate detection via SHA256 fingerprints, static file mount
- `backend/rag.py` — all RAG logic: ChromaDB vector store, LangGraph agentic loop with `retrieve_documents` tool, confidence scoring
- `backend/config.py` — all constants (models, chunk size, thresholds, limits)
- `backend/.env` — must contain `OPENAI_API_KEY`
- `backend/tests/test_ingest.py` — unit tests for hash persistence
- `frontend/src/app/page.tsx` — single-page UI (drag-and-drop PDF upload + query textarea)

**RAG pipeline details:**
- Embedding model: `text-embedding-3-small`
- LLM: `gpt-4o-mini`
- Chunk size: 1000 chars, overlap: 200
- Top-K retrieval: 10 documents
- Confidence threshold: 0.7 (answers below this return a fallback message)
- Duplicate detection: SHA256 hash stored in `backend/data/fingerprints.json`

**Persistence:** ChromaDB data lives in `backend/chroma_db/` and uploaded PDFs in `backend/data/`; both are Docker named volumes so data survives container restarts.

## Logging

Log level is controlled by the `LOG_LEVEL` env var in `backend/.env` (default: `INFO`). Set to `DEBUG` for detailed pipeline logs (PDF parsing, chunk counts, similarity search, confidence scores).

## Next.js note

This project uses Next.js 16 with Turbopack. APIs and conventions differ from older versions. Before writing frontend code, check `node_modules/next/dist/docs/` for current guidance.

## Testing rules

**Every new feature must have a corresponding test.** No exceptions.

- Place tests in `backend/tests/` for backend changes
- Use `pytest` with `unittest.mock.patch` for isolating file I/O and external services
- Run tests with `cd backend && uv run pytest` before submitting
- Tests must pass before a PR is merged
