"""answer.py — Module 2 Step 5: advanced retrieval (hybrid + rerank) -> grounded, cited answer.

The retrieval half is now the full Module 2 pipeline: hybrid_search (vector + keyword + RRF)
then cross-encoder rerank. The generation half (grounded prompt -> azure-brain) is unchanged.

Quick test:
    PYTHONPATH=backend python -m rag.answer "what is reciprocal rank fusion?"
"""
import os
from openai import OpenAI

from rag.hybrid import hybrid_search
from rag.rerank import rerank

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:4000/v1")
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "sk-local-anything")
ANSWER_MODEL = "default-brain"  # local: the Azure deployment is currently timing out; flip to "azure-brain" when healthy

# Bound the call so a stalled model fails fast (the try/except returns a readable message)
# instead of hanging the request. CPU-local generation can be slowish, so allow 60s.
_client = OpenAI(base_url=GATEWAY_URL, api_key=GATEWAY_API_KEY, timeout=60, max_retries=0)

# The grounding instruction — the heart of honest RAG: stay in the context, admit ignorance, cite.
SYSTEM_PROMPT = (
    "You answer using ONLY the numbered context passages provided. "
    "If the answer is not in the context, say you don't know — do not invent anything. "
    "After your answer, cite the passages you used like [1], [2]."
)


def answer(query: str, k: int = 5, candidates: int = 20) -> dict:
    """Advanced retrieval -> grounded prompt -> cited answer."""
    # Module 2 pipeline: hybrid (vector + keyword + RRF) -> cross-encoder rerank -> top-k.
    hits = rerank(query, hybrid_search(query, candidates=candidates), top_k=k)
    if not hits:
        return {"answer": "No documents have been ingested yet.", "sources": []}

    # Number each chunk so the model can refer to it as [n].
    context = "\n\n".join(f"[{i}] {h['text']}" for i, h in enumerate(hits, start=1))
    user_prompt = (
        f"Context passages:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the context above, and cite passages like [1], [2]."
    )

    try:
        resp = _client.chat.completions.create(
            model=ANSWER_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        answer_text = resp.choices[0].message.content
    except Exception as e:
        # Surface errors to the UI as a normal response (keeps CORS headers, avoids "Failed to fetch").
        answer_text = f"Answer generation failed ({type(e).__name__}): {e}"

    return {
        "answer": answer_text,
        "sources": [
            {"n": i, "title": h["title"], "score": round(h.get("rerank_score", 0.0), 3)}
            for i, h in enumerate(hits, start=1)
        ],
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "what is reciprocal rank fusion?"
    result = answer(q)
    print("ANSWER:\n" + result["answer"])
    print("\nSOURCES:")
    for s in result["sources"]:
        print(f"  [{s['n']}] {s['title']} (score {s['score']})")
