"""
backend/main.py — the FastAPI "waiter" for Module 0.

In Module 0 this backend does ONE thing: receive a question over HTTP and relay it
to the LiteLLM gateway, then return the answer. It NEVER names a provider — it only
ever asks the gateway for the nickname "default-brain". All the real AI logic
(RAG, agents, memory, ...) gets added INSIDE this backend in later modules.
"""

import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

from rag.answer import answer as rag_answer  # Module 1 RAG: retrieve -> grounded, cited answer

# --- Where the GATEWAY lives. Note: this is the gateway, never a provider. -------------
# /v1 is included because the OpenAI SDK appends "/chat/completions" to the base_url.
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:4000/v1")
# Our gateway has no master key set, so any non-empty string is accepted as the key.
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "sk-local-anything")
# The NICKNAME we ask for. The gateway's config decides which real model this becomes.
DEFAULT_MODEL = "default-brain"

# The standard OpenAI client — but pointed at OUR gateway instead of api.openai.com.
# This works ONLY because the gateway speaks the OpenAI dialect.
client = OpenAI(base_url=GATEWAY_URL, api_key=GATEWAY_API_KEY)

app = FastAPI(title="Everything App - Module 0 backend")

# Allow the Next.js dev server (http://localhost:3000) to call this backend from the
# browser. Browsers block cross-origin requests unless the server opts in via CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Shape of the JSON body the frontend POSTs: {"message": "..."}."""
    message: str


# ─────────────────────────────────────────────────────────────────────────────────────
#  ask_gateway — Module 0 "one function by hand". Written with Claude this time (see git
#  history); at the Module 0 checkpoint, Dev explains these 3 lines in his own words.
#
#  CONTRACT:  message (str) -> ask the gateway for DEFAULT_MODEL -> return reply text (str)
# ─────────────────────────────────────────────────────────────────────────────────────
def ask_gateway(message: str) -> str:
    # 1. Wrap the question in the chat format: a list of "turns". Here, one turn,
    #    spoken by the human, so role="user" and content is the question itself.
    messages = [{"role": "user", "content": message}]

    # 2. Send it to the GATEWAY via the OpenAI SDK. We ask for the NICKNAME
    #    DEFAULT_MODEL ("default-brain") — never a provider. `client` is already
    #    pointed at http://localhost:4000/v1, so this HTTP call lands on our gateway.
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
    )

    # 3. The reply text lives at choices[0].message.content — the same path as the
    #    JSON we saw in the PowerShell tests, just via dot-access on the SDK object.
    return response.choices[0].message.content


@app.post("/chat")
def chat(req: ChatRequest):
    """Relay endpoint: take the question, hand it to ask_gateway(), return the answer."""
    answer = ask_gateway(req.message)
    return {"answer": answer}


def stream_gateway(message: str):
    """Generator: yield the reply piece-by-piece as the gateway produces it."""
    messages = [{"role": "user", "content": message}]
    # stream=True -> the SDK returns an ITERATOR of chunks instead of one final object.
    stream = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        # Each chunk carries a small `delta`. On some chunks delta.content is None,
        # so we guard before forwarding.
        delta = chunk.choices[0].delta.content
        if delta:
            # JSON-encode the delta so tokens containing newlines or quotes can't break
            # the SSE line framing. The client does JSON.parse() to recover exact text.
            yield f"data: {json.dumps(delta)}\n\n"
    # Sentinel so a client knows the stream is finished.
    yield "data: [DONE]\n\n"


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """Streaming relay: same call as /chat but tokens arrive live via Server-Sent Events."""
    return StreamingResponse(stream_gateway(req.message), media_type="text/event-stream")


@app.post("/ask")
def ask(req: ChatRequest):
    """Module 1 RAG endpoint: retrieve relevant chunks, answer from them.
    Returns {"answer": str, "sources": [{n, title, distance}, ...]}."""
    return rag_answer(req.message)


@app.get("/health")
def health():
    """Trivial liveness check, so we can confirm the server is up before testing /chat."""
    return {"status": "ok"}
