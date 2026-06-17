"""hybrid.py — Module 2 Step 2: hybrid search via Reciprocal Rank Fusion (RRF).

Merges two ranked lists — vector (retrieve) + keyword (keyword_search) — into one
fused ranking. RRF score for a chunk = sum of 1/(RRF_K + rank) over the lists it appears in.

Quick test:
    PYTHONPATH=backend python -m rag.hybrid "what is RRF?"
"""
import sys

from rag.retrieve import retrieve
from rag.keyword import keyword_search

RRF_K = 60  # RRF dampening constant (standard default); higher = top ranks matter a bit less


def hybrid_search(query: str, k: int = 5, candidates: int = 20) -> list[dict]:
      vec_hits = retrieve(query, candidates)        # vector list, nearest first
      kw_hits = keyword_search(query, candidates)   # keyword list, best first
      
      scores = {}   # chunk text -> fused RRF score
      titles = {}   # chunk text -> its document title (to rebuild results later)

      for rank, hit in enumerate(vec_hits, start=1):
        scores[hit["text"]] = scores.get(hit["text"], 0) + 1 / (RRF_K + rank)
        titles[hit["text"]] = hit["title"]

      for rank, hit in enumerate(kw_hits, start=1):
        scores[hit["text"]] = scores.get(hit["text"], 0) + 1 / (RRF_K + rank)
        titles[hit["text"]] = hit["title"]
        
      ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

      return [
          {"text": text, "title": titles[text], "rrf_score": score}
          for text, score in ranked[:k]
      ]

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "what is RRF?"
    hits = hybrid_search(q)
    for i, r in enumerate(hits, 1):
        print(f"{i}. rrf={r['rrf_score']:.4f}  [{r['title']}]  {r['text'][:80]!r}")
