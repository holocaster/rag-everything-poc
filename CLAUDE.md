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
```

## Architecture

Two-stage Docker build: Node 22 builds the Next.js frontend as static files (`next build` with `output: 'export'`), then Python 3.12 serves them alongside the FastAPI backend via `StaticFiles`.

**Request flow:**
1. Browser hits `GET /` — served as static HTML from `/app/static` (compiled Next.js `out/`)
2. Browser calls `POST /ingest` (upload PDF) or `POST /query` (ask a question) — handled by FastAPI
3. `main.py` delegates to `rag.py`, which uses **agno** to embed the PDF into ChromaDB and query via `gpt-4o`

**Key files:**
- `backend/main.py` — FastAPI app: `/ingest` and `/query` endpoints + static file mount
- `backend/rag.py` — all RAG logic: ChromaDB vector store, agno `Knowledge` + `Agent` wired to `gpt-4o`
- `backend/.env` — must contain `OPENAI_API_KEY`
- `frontend/src/app/page.tsx` — single-page UI (PDF upload + query textarea)

**Persistence:** ChromaDB data lives in `backend/chroma_db/` and uploaded PDFs in `backend/data/`; both are bind-mounted in docker-compose so data survives container restarts.

## Next.js note

This project uses Next.js 16 with Turbopack. APIs and conventions differ from older versions. Before writing frontend code, check `node_modules/next/dist/docs/` for current guidance.
