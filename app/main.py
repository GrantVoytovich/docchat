"""FastAPI server for DocChat — upload a PDF, ask grounded questions."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .rag import DocIndex, answer, have_api_key, GEN_MODEL

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="DocChat")

# Single in-memory index (one document at a time — fine for a demo).
STATE: dict = {"index": None}


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a .pdf file.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        index = DocIndex.build(file.filename, tmp_path)
    except ValueError as e:
        raise HTTPException(422, str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    STATE["index"] = index
    return {"name": index.name, "pages": index.pages, "chunks": len(index.chunks),
            "has_key": have_api_key(), "model": GEN_MODEL}


class Query(BaseModel):
    question: str
    k: int = 5


@app.post("/api/query")
async def query(q: Query):
    index = STATE["index"]
    if index is None:
        raise HTTPException(400, "Upload a PDF first.")
    if not q.question.strip():
        raise HTTPException(400, "Ask a question.")
    hits = index.search(q.question, k=max(1, min(q.k, 8)))
    result = answer(q.question, hits)
    sources = [{"n": i + 1, "page": h.chunk.page, "score": round(h.score, 3),
                "text": h.chunk.text} for i, h in enumerate(hits)]
    return JSONResponse({"answer": result["answer"], "needs_key": result["needs_key"],
                         "model": result["model"], "sources": sources})


app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")
