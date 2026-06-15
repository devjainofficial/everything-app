"""embed.py — turn text into vectors. This is a MODEL call, so it goes through the GATEWAY."""
import os
from openai import OpenAI

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:4000/v1")
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "sk-local-anything")
EMBED_MODEL = "embedder"  # gateway nickname -> ollama/nomic-embed-text (768-dim)

# Same OpenAI SDK as chat — just pointed at the gateway, and using .embeddings not .chat.
_client = OpenAI(base_url=GATEWAY_URL, api_key=GATEWAY_API_KEY)


def embed_one(text: str) -> list[float]:
    """Embed a single string into one 768-dim vector (via the gateway)."""
    # encoding_format="float": the OpenAI SDK defaults to base64 embeddings, which the
    # local Ollama backend doesn't support — so we explicitly request plain floats.
    resp = _client.embeddings.create(model=EMBED_MODEL, input=text, encoding_format="float")
    return resp.data[0].embedding


def vector_literal(vec: list[float]) -> str:
    """Format a Python float list as a pgvector text literal: '[0.1,0.2,...]'.
    Inserted with a `::vector` cast so Postgres stores it in the vector column."""
    return "[" + ",".join(repr(float(x)) for x in vec) + "]"
