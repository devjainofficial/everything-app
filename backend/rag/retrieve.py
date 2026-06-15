"""retrieve.py — Module 1 "one function by hand": semantic (vector) search over chunks.

Quick test from the project root:
    PYTHONPATH=backend python -m rag.retrieve "what is reciprocal rank fusion?"
"""
import sys

from rag.db import get_conn
from rag.embed import embed_one, vector_literal


def retrieve(query: str, k: int = 5) -> list[dict]:
    qvec = embed_one(query)
    qlit = vector_literal(qvec)

    sql = """
        select c.text, d.title, c.embedding <=> %s::vector as distance
        from chunks c
        join documents d on d.id = c.document_id
        order by c.embedding <=> %s::vector
        limit %s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (qlit, qlit, k))
        rows = cur.fetchall()

    return [
        {"text": text, "title": title, "distance": distance}
        for (text, title, distance) in rows
    ]

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "what is RRF?"
    for i, r in enumerate(retrieve(q), 1):
        print(f"{i}. dist={r['distance']:.4f}  [{r['title']}]  {r['text'][:80]!r}")
