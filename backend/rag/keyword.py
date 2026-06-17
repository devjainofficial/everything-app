"""keyword.py — Module 2 Step 1: keyword (full-text) search over chunks.

Postgres full-text search is the "keyword" half of hybrid search. It matches the query's
TERMS (not its meaning), so it catches exact tokens vector search can drift on — e.g.
"RRF", "BM25", function names, error codes.

Quick test:
    PYTHONPATH=backend python -m rag.keyword "RRF"
"""
import sys

from rag.db import get_conn


def keyword_search(query: str, k: int = 5) -> list[dict]:
    """Return the k chunks best matching the query's TERMS, ranked by full-text relevance."""
    sql = """
        select c.text, d.title,
               ts_rank(c.text_tsv, websearch_to_tsquery('english', %s)) as score
        from chunks c
        join documents d on d.id = c.document_id
        where c.text_tsv @@ websearch_to_tsquery('english', %s)   -- keep only rows that match the terms
        order by score desc
        limit %s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (query, query, k))
        rows = cur.fetchall()
    return [{"text": t, "title": ti, "score": float(s)} for (t, ti, s) in rows]


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "RRF"
    hits = keyword_search(q)
    if not hits:
        print(f"(no keyword matches for {q!r})")
    for i, r in enumerate(hits, 1):
        print(f"{i}. score={r['score']:.4f}  [{r['title']}]  {r['text'][:80]!r}")
