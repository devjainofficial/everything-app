"""rerank.py — Module 2 Step 3: cross-encoder reranking of a candidate shortlist.

A cross-encoder reads each (query, chunk) pair TOGETHER and scores true relevance,
then we reorder. Run this only on the small shortlist from hybrid_search, never the
whole corpus (it's far more expensive than vector/keyword retrieval).

Quick test:
    PYTHONPATH=backend python -m rag.rerank "what is RRF?"
"""
import sys

# Small, fast, CPU-friendly cross-encoder trained for search relevance.
_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model = None  # lazy-loaded: don't pull the model into memory until the first rerank call


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder  # imported lazily so the dep is optional
        _model = CrossEncoder(_MODEL_NAME)               # downloads ~80MB on first use
    return _model


def rerank(query: str, hits: list[dict], top_k: int = 5) -> list[dict]:
    """Re-score (query, chunk) pairs with the cross-encoder; return the top_k most relevant."""
    if not hits:
        return []
    model = _get_model()
    pairs = [(query, h["text"]) for h in hits]   # one (query, chunk) pair per candidate
    scores = model.predict(pairs)                # higher = more relevant
    for h, s in zip(hits, scores):
        h["rerank_score"] = float(s)
    return sorted(hits, key=lambda h: h["rerank_score"], reverse=True)[:top_k]


if __name__ == "__main__":
    from rag.hybrid import hybrid_search
    q = sys.argv[1] if len(sys.argv) > 1 else "what is RRF?"
    shortlist = hybrid_search(q, k=20)           # fused candidates...
    for i, r in enumerate(rerank(q, shortlist), 1):  # ...reordered by the cross-encoder
        print(f"{i}. rerank={r['rerank_score']:.3f}  [{r['title']}]  {r['text'][:80]!r}")
