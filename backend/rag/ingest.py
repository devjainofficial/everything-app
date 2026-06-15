"""ingest.py — Module 1 ingest pipeline: file -> text -> chunks -> embeddings -> pgvector.

Run from the project root:
    PYTHONPATH=backend python -m rag.ingest data/sample.md
"""
import sys
from pathlib import Path

from rag.db import get_conn
from rag.embed import embed_one, vector_literal


def extract_text(path: str) -> str:
    """Pull plain text out of a file. PDFs via pypdf; everything else read as UTF-8 text."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        # extract_text() can return None for image-only pages, so coalesce to "".
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return p.read_text(encoding="utf-8")


def chunk_text(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    """Naive fixed-window chunker: ~`size` chars per chunk, carrying `overlap` chars
    forward so an idea isn't guillotined at a boundary. Deliberately simple for Module 1."""
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap            # advance, leaving `overlap` chars of carry-over
    return [c.strip() for c in chunks if c.strip()]


def ingest_file(path: str, title: str | None = None) -> dict:
    """Ingest one file: store a documents row, then one chunks row (text + embedding) each."""
    title = title or Path(path).name
    chunks = chunk_text(extract_text(path))
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "insert into documents (title, source_uri) values (%s, %s) returning id",
            (title, str(path)),
        )
        doc_id = cur.fetchone()[0]
        for i, chunk in enumerate(chunks):
            vec = embed_one(chunk)                       # text -> 768-dim vector (via gateway)
            cur.execute(
                "insert into chunks (document_id, ordinal, text, embedding) "
                "values (%s, %s, %s, %s::vector)",        # ::vector casts the literal into the column type
                (doc_id, i, chunk, vector_literal(vec)),
            )
        conn.commit()
    return {"document_id": doc_id, "title": title, "chunks": len(chunks)}


if __name__ == "__main__":
    print(ingest_file(sys.argv[1]))
