# 📄 DocChat — RAG over a PDF

Upload a PDF and ask questions. DocChat **chunks and embeds** the document,
**retrieves** the passages most relevant to your question, and has **Claude answer
using only those passages, with citations**. Every claim points back to a numbered
source you can read — no ungrounded answers.

## The RAG pipeline

```
PDF → text per page → overlapping chunks → local embeddings
    → cosine-similarity retrieval (top-k) → grounded answer from Claude + citations
```

- **Retrieval is local and free** — a `sentence-transformers` model (`all-MiniLM-L6-v2`)
  embeds chunks and the query; cosine similarity ranks passages. No API key needed.
- **Generation uses Claude** — the retrieved passages (and only those) are sent to the
  model with instructions to answer from them and cite each claim as `[n]`.
- **Key-ready:** with no `ANTHROPIC_API_KEY` the app still runs retrieval and shows the
  passages it found; set a key to turn on the written answers.

## Setup & run

```powershell
cd C:\Users\grant\docchat
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# optional — enables Claude's grounded answers (retrieval works without it):
$env:ANTHROPIC_API_KEY = "sk-ant-..."
# optional — cheaper model for testing: $env:ANTHROPIC_MODEL = "claude-haiku-5-5"

uvicorn app.main:app --reload --port 8040
```

Open <http://localhost:8040>, upload a PDF, and ask. First run downloads the
embedding model (~90 MB).

## Notes & honest limits

- One document in memory at a time (fine for a demo; a real deployment would use a
  vector store + per-user sessions).
- Works on **text** PDFs; scanned-image PDFs need OCR first.
- Default model is `claude-opus-5-5` (override with `ANTHROPIC_MODEL`).

## Next steps

- Persistent vector store (FAISS / pgvector) and multi-document corpora.
- Streaming answers; re-ranking; hybrid (keyword + vector) retrieval.
