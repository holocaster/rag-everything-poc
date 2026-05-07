from contextlib import asynccontextmanager
import hashlib
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import rag

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent / "data"
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_FINGERPRINT_FILE = _DATA_DIR / config.FINGERPRINT_FILE


def _load_hashes() -> set[str]:
    if _FINGERPRINT_FILE.exists():
        hashes = set(json.loads(_FINGERPRINT_FILE.read_text()))
        logger.debug("loaded %d hashes", len(hashes))
        return hashes
    return set()


def _save_hashes(hashes: set[str]) -> None:
    _FINGERPRINT_FILE.write_text(json.dumps(sorted(hashes)))
    logger.debug("saved %d hashes", len(hashes))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app starting")
    load_dotenv()
    _DATA_DIR.mkdir(exist_ok=True)
    logger.info("app ready")
    yield


app = FastAPI(lifespan=lifespan)


class QueryRequest(BaseModel):
    question: str


@app.post("/ingest")
async def ingest(file: UploadFile):
    if not (file.filename or "").lower().endswith(config.ACCEPTED_FILE_TYPES):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    logger.debug("ingest request: file=%s size=%d", file.filename, len(contents))

    if len(contents) > config.FILE_SIZE_LIMIT:
        raise HTTPException(status_code=413, detail=f"File exceeds the {config.FILE_SIZE_LIMIT // (1024 * 1024)} MB limit")

    file_hash = hashlib.sha256(contents).hexdigest()
    if file_hash in _load_hashes():
        logger.info("duplicate file skipped: %s", file.filename)
        raise HTTPException(status_code=409, detail="This PDF has already been ingested")

    dest = _DATA_DIR / file.filename
    dest.write_bytes(contents)

    try:
        logger.debug("calling rag.ingest: %s", dest)
        rag.ingest(str(dest))
    except Exception as e:
        logger.error("ingest failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    hashes = _load_hashes()
    hashes.add(file_hash)
    _save_hashes(hashes)

    logger.info("ingest complete: %s", file.filename)
    return {"message": "ingested", "filename": file.filename}


@app.post("/query")
async def query(request: QueryRequest):
    logger.debug("query: %r", request.question)
    try:
        answer = rag.query(request.question)
    except Exception as e:
        logger.error("query failed", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    logger.info("query answered")
    return {"answer": answer}


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

if _STATIC_DIR.is_dir():

    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            response = await super().get_response(path, scope)
            if response.status_code == 404:
                return await super().get_response("index.html", scope)
            return response

    app.mount("/", SPAStaticFiles(directory=_STATIC_DIR, html=True), name="static")
else:

    @app.get("/")
    def index():
        return JSONResponse({"message": "hello world"})
