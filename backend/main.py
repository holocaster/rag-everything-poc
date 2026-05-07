from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import rag

_DATA_DIR = Path(__file__).resolve().parent / "data"
_STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    _DATA_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)


class QueryRequest(BaseModel):
    question: str


@app.post("/ingest")
async def ingest(file: UploadFile):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MB limit")

    dest = _DATA_DIR / file.filename
    dest.write_bytes(contents)

    try:
        rag.ingest(str(dest))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "ingested", "filename": file.filename}


@app.post("/query")
async def query(request: QueryRequest):
    try:
        answer = rag.query(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
