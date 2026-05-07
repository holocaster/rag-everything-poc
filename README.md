# rag-everything-poc

Upload PDFs and ask questions about them. FastAPI backend with RAG via LangChain + ChromaDB, Next.js frontend.

## Quick start

```bash
# 1. Add your OpenAI key
echo "OPENAI_API_KEY=sk-..." > backend/.env

# 2. Build and run
docker compose up --build
```

Open http://localhost:8000, upload a PDF, then ask questions.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js (static export, served by FastAPI) |
| Backend | FastAPI + Python 3.12 |
| RAG | LangChain + LangGraph, `gpt-4o-mini`, `text-embedding-3-small` |
| Vector store | ChromaDB (persisted in Docker volume) |

## Dev mode

```bash
# Backend (requires backend/.env)
cd backend && uv sync && uv run uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Logging

Set `LOG_LEVEL=DEBUG` in `backend/.env` to see detailed pipeline logs (PDF parsing, chunk counts, confidence scores, etc.). Default level is `INFO`.

## Persistence

`backend/data/` (uploaded PDFs) and `backend/chroma_db/` (vector store) are stored in Docker named volumes and survive container restarts.
