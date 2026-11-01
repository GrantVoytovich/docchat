"""
A small, honest RAG pipeline for "chat with a PDF".

    PDF -> text per page -> overlapping chunks -> embeddings (local, free)
        -> cosine-similarity retrieval -> grounded answer from Claude, with citations.

The retrieval half runs entirely locally (sentence-transformers), so it works with
no API key. Only the final answer step calls Claude; without a key the API returns
the retrieved passages so the retrieval is still demonstrable.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEN_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5-5")
CHUNK_CHARS = 900
CHUNK_OVERLAP = 150
TOP_K = 5

_embedder = None


def _get_embedder():
    """Load the embedding model once (downloads ~90 MB on first use)."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def embed(texts: list[str]) -> np.ndarray:
    vecs = _get_embedder().encode(texts, normalize_embeddings=True,
                                  show_progress_bar=False, convert_to_numpy=True)
    return np.asarray(vecs, dtype=np.float32)


@dataclass
class Chunk:
    id: int
    page: int
    text: str


def _split_page(text: str) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    out, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        # prefer to break on a sentence/space boundary
        if end < len(text):
            dot = text.rfind(". ", start + CHUNK_CHARS // 2, end)
            if dot != -1:
                end = dot + 1
        out.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return [c for c in out if c]


def chunk_pdf(path: str) -> list[Chunk]:
    from pypdf import PdfReader
    reader = PdfReader(path)
    chunks: list[Chunk] = []
    for pnum, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        for piece in _split_page(txt):
            chunks.append(Chunk(id=len(chunks), page=pnum, text=piece))
    return chunks


@dataclass
class Hit:
    chunk: Chunk
    score: float


class DocIndex:
    """One document's chunks + their embeddings, with cosine search."""

    def __init__(self, name: str, chunks: list[Chunk], matrix: np.ndarray):
        self.name = name
        self.chunks = chunks
        self.matrix = matrix            # (n_chunks, dim), rows L2-normalized
        self.pages = (chunks[-1].page if chunks else 0)

    @classmethod
    def build(cls, name: str, path: str) -> "DocIndex":
        chunks = chunk_pdf(path)
        if not chunks:
            raise ValueError("No extractable text found — this PDF may be scanned "
                             "images (OCR would be needed) rather than text.")
        matrix = embed([c.text for c in chunks])
        return cls(name, chunks, matrix)

    def search(self, query: str, k: int = TOP_K) -> list[Hit]:
        q = embed([query])[0]
        scores = self.matrix @ q         # cosine (rows are normalized)
        order = np.argsort(-scores)[:k]
        return [Hit(self.chunk_by_row(int(i)), float(scores[int(i)])) for i in order]

    def chunk_by_row(self, row: int) -> Chunk:
        return self.chunks[row]


SYSTEM_PROMPT = (
    "You answer questions strictly from the provided excerpts of a document. "
    "Use only what the excerpts say — do not add outside knowledge. Cite every "
    "claim with the passage number in square brackets, like [1] or [2][4]. "
    "If the excerpts do not contain the answer, say so plainly instead of guessing. "
    "Keep answers concise."
)


def have_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def answer(question: str, hits: list[Hit]) -> dict:
    """Generate a grounded answer from the retrieved passages via Claude.

    Returns {answer, model} or, with no key, {answer: None, needs_key: True}.
    """
    context = "\n\n".join(
        f"[{i+1}] (p.{h.chunk.page}) {h.chunk.text}" for i, h in enumerate(hits)
    )
    if not have_api_key():
        return {"answer": None, "needs_key": True, "model": GEN_MODEL}

    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=GEN_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (f"Excerpts:\n\n{context}\n\n"
                        f"Question: {question}\n\n"
                        "Answer using only the excerpts above, with [n] citations."),
        }],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    return {"answer": text, "needs_key": False, "model": GEN_MODEL}
