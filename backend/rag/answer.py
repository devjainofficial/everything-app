"""answer.py — Module 1 Step 5: retrieve chunks -> grounded prompt -> cited answer.

This is the "generation" half of RAG. It calls retrieve() (your by-hand function),
puts the chunks into the prompt as numbered context, and asks the model to answer
using ONLY that context and cite the passages it used.

Quick test from the project root:
    PYTHONPATH=backend python -m rag.answer "what is reciprocal rank fusion?"
"""
import os
from openai import OpenAI

from rag.retrieve import retrieve

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:4000/v1")
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "sk-local-anything")
ANSWER_MODEL = "azure-brain"   # gateway nickname; swap to "default-brain" for free/local

_client = OpenAI(base_url=GATEWAY_URL, api_key=GATEWAY_API_KEY)

# The grounding instruction — the heart of honest RAG: stay in the context, admit ignorance, cite.
SYSTEM_PROMPT = (
    "You answer using ONLY the numbered context passages provided. "
    "If the answer is not in the context, say you don't know — do not invent anything. "
    "After your answer, cite the passages you used like [1], [2]."
)


def answer(query: str, k: int = 5) -> dict:
    """Retrieve top-k chunks, ground a prompt on them, and return a cited answer."""
    hits = retrieve(query, k)                       # <- your Step 4 function
    if not hits:
        return {"answer": "No documents have been ingested yet.", "sources": []}

    # Number each chunk so the model can refer to it as [n].
    context = "\n\n".join(f"[{i}] {h['text']}" for i, h in enumerate(hits, start=1))
    user_prompt = (
        f"Context passages:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the context above, and cite passages like [1], [2]."
    )

    # Generation call -> through the gateway -> azure-brain (gpt-4.1).
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
        # Surface the error to the UI as a normal response (keeps CORS headers, avoids
        # the opaque browser "Failed to fetch"). Common cause: answer model not loaded.
        answer_text = f"Answer generation failed ({type(e).__name__}): {e}"

    return {
        "answer": answer_text,
        # Hand back what we cited, so the UI can show sources.
        "sources": [
            {"n": i, "title": h["title"], "distance": round(h["distance"], 4)}
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
        print(f"  [{s['n']}] {s['title']} (dist {s['distance']})")
