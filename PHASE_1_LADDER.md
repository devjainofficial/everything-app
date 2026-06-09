# Everything App, Phase 1 Learning Ladder (Modules 0 to 3)

How to run this ladder, the reward loop:
1. LEARN first. Read or skim the resources for the module BEFORE Claude Code
   writes a single line. You cannot understand or debug what gets built if you
   have not seen the idea first. This is the whole point.
2. BUILD with Claude Code, following the CLAUDE.md discipline (spec first, teach
   before code, annotate every line, one function by hand).
3. UNLOCK the next module by passing this module's Reasoning Checkpoint out loud,
   no AI open. The full checkpoint is in your PRD. Come back to your mentor chat
   to get the checkpoint graded before you advance.

Note: official docs beat random tutorials, which is why almost every link here
is a primary source.

---

## Module 0, Foundations + LiteLLM gateway

LEARN FIRST
- LiteLLM Proxy quick start (your gateway):
  https://docs.litellm.ai/docs/proxy/quick_start
- LiteLLM Azure provider page (how your company deployment plugs in: it is
  configured as model: azure/<your-deployment-name> with api_base, api_key,
  api_version):
  https://docs.litellm.ai/docs/providers/azure
- Vercel "AI SDK Python Streaming" template. This IS your architecture: a
  Next.js + useChat frontend talking to a Python FastAPI backend with token
  streaming. Read how the two connect:
  https://vercel.com/templates/ai/ai-sdk-python-streaming
- Anthropic, "Building Effective Agents" (read the intro and "When to use
  agents"). Their principle, start simple and call the API directly before
  frameworks, is the spirit of this whole project:
  https://www.anthropic.com/research/building-effective-agents

BUILD: PRD Module 0. FastAPI service + Next.js shell over streaming, every model
call routed through a self-hosted LiteLLM gateway, with your Azure deployment and
a local Ollama model both swappable by config alone.

WATCH OUT: keep your real AZURE_API_KEY in a .env file that is gitignored. The
gateway reads it from the environment (os.environ/AZURE_API_KEY in the config),
so the key never sits in your code or your git history.

UNLOCK: explain why every call routes through the gateway, what it abstracts,
what breaks if you bypass it for one call, and how you swap the default model
with zero code changes.

---

## Module 1, Naive RAG

LEARN FIRST
- Supabase, "Semantic search" (pgvector, embeddings, the match function,
  distance operators; note the warning to use the same embedding model for
  everything you compare):
  https://supabase.com/docs/guides/ai/semantic-search
- Supabase, "AI & Vectors" overview for the bigger picture:
  https://supabase.com/docs/guides/ai

CONCEPT TO HOLD: an embedding is a numeric fingerprint of meaning. Vector search
finds the chunks whose fingerprints sit nearest your question's. Top-k cosine is
the simplest and weakest version of this.

BUILD: PRD Module 1. Ingest a few of your AI papers, chunk them, embed into
pgvector, retrieve top-k by cosine, stuff into the prompt, answer with citations.

WATCH OUT: this is meant to be the boring baseline. Do NOT add reranking or
hybrid search here. You need to feel naive RAG's failure modes on dense
technical PDFs before you earn the right to fix them in Module 2.

UNLOCK: walk a question from text to answer, say where embeddings come from, what
the vector index compares, why top-k cosine is weak, and name two failure modes
on technical PDFs.

---

## Module 2, Advanced retrieval (hybrid + rerank + contextual)

LEARN FIRST
- Supabase, "Hybrid search". This one literally implements tsvector keyword
  search + pgvector semantic search fused with Reciprocal Rank Fusion, which is
  your exact Module 2 target:
  https://supabase.com/docs/guides/ai/hybrid-search
- Sentence Transformers, "Retrieve & Re-Rank". The bi-encoder retrieves a
  candidate set, then a cross-encoder reranks it. Clear explanation plus a
  runnable notebook:
  https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
- Anthropic, "Introducing Contextual Retrieval". Prepend a short LLM-generated
  context blurb to each chunk before embedding so chunks do not lose their
  meaning when split:
  https://www.anthropic.com/news/contextual-retrieval

BUILD: PRD Module 2. BM25 + vector fused with RRF, then a cross-encoder rerank of
the shortlist, plus contextual retrieval at index time. Prove it beats Module 1
on your own questions.

WATCH OUT: a reranker only reranks what retrieval already found. If recall is
bad, no reranker saves you. So get hybrid retrieval right first, then rerank the
shortlist (the top 50 to 100), never the whole corpus.

UNLOCK: explain why BM25 + vectors beats either alone, what RRF does that
score-averaging does not, and the difference between the retriever and the
reranker and why you run both.

---

## Module 3, Tool calling + first single agent (ReAct)

LEARN FIRST
- Anthropic, "Building Effective Agents", the agent section: an agent is just an
  LLM calling tools in a loop based on feedback:
  https://www.anthropic.com/research/building-effective-agents
- Anthropic, "Writing effective tools for AI agents". Designing good tool schemas
  and descriptions is most of what makes tool calling actually work:
  https://www.anthropic.com/engineering/writing-tools-for-agents

CONCEPT TO HOLD: when the model "calls a tool" it just emits a structured
request. YOUR code executes the tool and feeds the result back as the next
observation. The loop is reason, act, observe, repeat, until a stop condition.

BUILD: PRD Module 3. One agent that calls tools (your retriever, a calculator) in
a reason-act-observe loop and decides when to stop.

WATCH OUT (important): write the raw while-loop yourself, with Claude Code
teaching you. Do NOT use a framework's prebuilt agent like LangGraph's
create_react_agent here. The point is to understand the loop from the inside. You
wrap it in LangGraph in Module 4, and it will feel transparent instead of magical
because you built the raw version first. This is also your "one function by hand"
for this module.

UNLOCK: say what the model actually emits on a tool call, who executes the tool,
draw the ReAct loop, and point to where an infinite loop could form.