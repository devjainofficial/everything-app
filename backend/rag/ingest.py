"""ingest.py — ingest pipeline: file -> text -> chunks -> (context) -> embeddings -> pgvector.

Module 2 adds CONTEXTUAL RETRIEVAL: before embedding, an LLM writes a one-sentence
context that situates each chunk in its document; we embed (context + chunk) so the
vector captures what the chunk is ABOUT. The original chunk text is still stored for citation.

Run from the project root:
    PYTHONPATH=backend python -m rag.ingest data/sample.md
"""
import os
import sys
from pathlib import Path

from openai import OpenAI

from rag.db import get_conn
from rag.embed import embed_one, vector_literal

# Chat client (for context generation) -> through the gateway.
_chat = OpenAI(
    base_url=os.environ.get("GATEWAY_URL", "http://localhost:4000/v1"),
    api_key=os.environ.get("GATEWAY_API_KEY", "sk-local-anything"),
)
# Per-chunk context generation is HIGH-VOLUME, so we use the local model: free, no API
# rate limits (Azure 429s on batch calls). The guard in make_context() drops any malformed
# or prompt-echoing output, so the cheap model's occasional flakiness can't poison embeddings.
CONTEXT_MODEL = "default-brain"


def extract_text(path: str) -> str:
    """Pull plain text out of a file. PDFs via pypdf; everything else read as UTF-8 text."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return p.read_text(encoding="utf-8")


def chunk_text(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    """Naive fixed-window chunker: ~`size` chars per chunk, carrying `overlap` chars forward."""
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


def make_context(doc_text: str, chunk: str) -> str:
    """Ask the LLM for ONE short sentence situating this chunk within its document.
    Returns "" if the model misbehaves (so we never poison the embedding with garbage)."""
    resp = _chat.chat.completions.create(
        model=CONTEXT_MODEL,
        messages=[
            {"role": "system", "content":
                "You write ONE short sentence that situates a chunk within its document, "
                "to improve search retrieval. Output only that sentence, no preamble."},
            {"role": "user", "content":
                f"<document>\n{doc_text}\n</document>\n\n"
                f"Chunk:\n{chunk}\n\n"
                "Write one short sentence situating this chunk within the document."},
        ],
    )
    ctx = (resp.choices[0].message.content or "").strip()
    # Defensive guard: if the model echoes the prompt or runs away, drop the context.
    if not ctx or len(ctx) > 300 or "<document>" in ctx:
        return ""
    return ctx


def ingest_file(path: str, title: str | None = None) -> dict:
    """Ingest one file with contextual retrieval: store chunk text + its context, embed both."""
    title = title or Path(path).name
    full_text = extract_text(path)
    chunks = chunk_text(full_text)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "insert into documents (title, source_uri) values (%s, %s) returning id",
            (title, str(path)),
        )
        doc_id = cur.fetchone()[0]
        for i, chunk in enumerate(chunks):
            context = make_context(full_text, chunk)             # situate the chunk (LLM via gateway)
            embed_input = f"{context}\n\n{chunk}" if context else chunk
            vec = embed_one(embed_input)                          # embed CONTEXT + CHUNK (or chunk alone)
            cur.execute(
                "insert into chunks (document_id, ordinal, text, context_text, embedding) "
                "values (%s, %s, %s, %s, %s::vector)",
                (doc_id, i, chunk, context, vector_literal(vec)),
            )
        conn.commit()
    return {"document_id": doc_id, "title": title, "chunks": len(chunks)}


if __name__ == "__main__":
    print(ingest_file(sys.argv[1]))
