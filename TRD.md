# Everything App, Technical Requirements Document (TRD)

> Companion to `PRD.md`. Source of truth for stack/modules/constraints: `CLAUDE.md`.
> **Constraints that shape every decision:** solo dev · capable reasoning on a company Azure OpenAI deployment via the LiteLLM gateway · small local Ollama models as the cheap tier · every model call through the gateway · one app, not 14 toys.
> Non-obvious choices carry a one-line **_why_** so the reasoning is learnable, not just the result.

---

## 1. System architecture (the parts)

Three processes plus one database, with the gateway as the single choke point for model calls:

```
┌─────────────────────────┐        ┌──────────────────────────────┐
│  Next.js (App Router)   │  HTTP  │   Python FastAPI, AI core    │
│  Tailwind + Vercel AI   │ ─────▶ │  agents · RAG · memory ·     │
│  SDK  (UI + streaming)  │ ◀───── │  evals · MCP servers         │
└─────────────────────────┘  SSE   └──────────────┬───────────────┘
                                                   │ all model calls
                                                   ▼
                                   ┌──────────────────────────────┐
                                   │  LiteLLM gateway (self-host)  │
                                   │  routes: Ollama | Azure/cloud │
                                   └───────┬───────────────┬───────┘
                                           ▼               ▼
                                   ┌────────────┐   ┌──────────────┐
                                   │  Ollama    │   │ Azure OpenAI │
                                   │ (local)    │   │ + cloud      │
                                   └────────────┘   └──────────────┘
                                                   ▲
        ┌──────────────────────────────────────────┴───────────────┐
        ▼                                                           ▼
┌──────────────────────────────┐                       ┌────────────────────────┐
│ Supabase Postgres + pgvector │                       │ Langfuse (self-hosted) │
│ docs·chunks·embeddings·      │                       │ traces / spans / cost  │
│ memories·traces·checkpoints  │                       └────────────────────────┘
└──────────────────────────────┘
```

- **Frontend, Next.js App Router + Tailwind + Vercel AI SDK.** UI and token streaming **only**; no agent logic here. _Why: keep all reasoning server-side in Python so there's one place to read, test, and debug, the browser never makes model decisions._
- **AI core, Python + FastAPI.** Hosts agents, RAG, memory, evals, and MCP servers. _Why: the LLM ecosystem (LangGraph, Ragas/DeepEval, DSPy) is Python-native; fighting that in JS would add friction with zero learning upside._
- **Gateway, self-hosted LiteLLM.** Every model call goes through it; providers (Ollama, Azure OpenAI, Claude, OpenAI) are swappable by config. _Why: no single provider becomes a hard dependency, and cost/routing/caching get one control point instead of being smeared across the code._ The Azure deployment is called by its deployment name and an API version through LiteLLM, with the API key in an environment variable, never committed to git.
- **Cloud brain, Azure OpenAI.** The default model for reasoning-heavy work (agent, orchestration, multi-agent, guardrail reasoning, DSPy), reached only through the gateway.
- **Local models, Ollama.** Small local models as the cheap tier (classification, query rewriting, drafts, light tasks). _Why: vLLM only wins under concurrent multi-user load you don't have (trap list); Ollama is the right local runtime for one user._
- **Data, Supabase Postgres + pgvector.** One database for documents, vectors, memory, traces metadata, and checkpoints. _Why: a dedicated vector DB is premature when Supabase is already running; one store means one mental model and joinable data._
- **Observability, Langfuse (self-hosted).** End-to-end traces, spans, cost, latency.
- **Evals, Ragas + DeepEval + Promptfoo.** Quality gate in CI.
- **Prompt optimization, DSPy (MIPROv2).** Module 13 only.

## 2. Request flow (UI → gateway → agent → data → back)

1. **UI →** User asks a question in the Next.js chat. Vercel AI SDK opens a streaming request to FastAPI. _Why streaming: the user sees tokens immediately and you learn SSE plumbing once, reused everywhere._
2. **Router (LangGraph) →** FastAPI enters the graph. A router node classifies intent and selects a path/subgraph. _Why a router: it's the seam where single-agent grows into multi-agent without rewrites._
3. **Retrieve →** The chosen path queries pgvector: hybrid (BM25 + vector) → RRF fuse → cross-encoder rerank. Relevant memories are pulled the same way.
4. **Reason/act (agent) →** The agent runs a ReAct loop; tool calls (retrieval, MCP-wrapped tools) execute in **your** code, results fed back as observations. Guardrails gate input, retrieved context, tool calls, and output.
5. **Model call →** Every generation/classification/embedding call exits through the **LiteLLM gateway**, which applies routing (small-local for cheap tasks vs. Azure/cloud for reasoning) and semantic caching.
6. **Persist →** State checkpoints, new memories, and the run's trace/spans/cost are written (Postgres + Langfuse).
7. **→ Back to UI:** the answer streams back token-by-token with citations.

Every hop above is also a **span** in Langfuse, so the flow and its observability are the same diagram.

## 3. Module → component mapping

| Module | Primary component(s) | What it adds to the one app |
|---|---|---|
| 0 Foundations + gateway | LiteLLM, FastAPI, Next.js shell | The skeleton + single model choke point |
| 1 Naive RAG | pgvector, FastAPI ingest/retrieve | Baseline retrieve→stuff→answer |
| 2 Advanced retrieval | pgvector (BM25+vector), reranker | Hybrid + RRF + cross-encoder + contextual |
| 3 Tool calling / ReAct | FastAPI agent loop | First single agent with tools |
| 4 Orchestration | LangGraph | Explicit state, router, checkpoints, HITL |
| 5 MCP server | FastAPI MCP server + Inspector | Tools exposed as a protocol |
| 6 Memory | pgvector (memories), Mem0 compare | Episodic/semantic/long-term layer |
| 7 Multi-agent | LangGraph supervisor + subgraphs | Supervisor dispatch to specialists |
| 8 Evaluation | Ragas + DeepEval + Promptfoo | Golden dataset + CI quality gate |
| 9 Observability | Langfuse | End-to-end traces/spans/cost |
| 10 Guardrails | FastAPI gate functions | 4-point gating + injection defense |
| 11 Optimization | LiteLLM (cache + routing) | Cheaper/faster, proven by evals |
| 12 Advanced capability | multimodal RAG **or** browser agent | One deferred advanced path |
| 13 DSPy | DSPy MIPROv2 | Optimized prompt/program vs. golden set |

_Why a mapping table: it makes the invariant explicit, every module lands on an existing component and is wired in, never bolted on as a separate demo._

## 4. Data model sketch (Postgres + pgvector)

One database, joinable. Vector columns use pgvector; `embedding` dims match the chosen embedding model.

- **documents.** `id, source_uri, title, doc_type ('pdf'|'md'|…), metadata jsonb, created_at`. The raw papers/docs.
- **chunks.** `id, document_id → documents, ordinal, text, context_text, token_count`. `context_text` = the contextual-retrieval prefix added at index time. _Why store context separately: you can A/B "with vs. without context" without re-chunking._
- **embeddings.** `id, chunk_id → chunks, model, embedding vector(N), created_at`. Separate table keyed by `model`. _Why split from chunks: lets you re-embed with a new model and keep both for comparison instead of destroying the old index._
- **memories.** `id, kind ('episodic'|'semantic'|'long_term'), content, embedding vector(N), salience, source_run_id, created_at, last_used_at`. Memory retrieved by the same vector search as documents but tagged by `kind`.
- **traces.** `id, run_id, request, final_response, total_cost, total_latency_ms, created_at` (+ Langfuse holds the rich span tree). _Why a thin local copy: cheap joins for evals/cost queries without calling the Langfuse API each time._
- **checkpoints.** `id, thread_id, graph_state jsonb, parent_id, created_at`. LangGraph state snapshots enabling pause/resume and HITL.
- **eval_runs / eval_cases.** `golden question, expected, retrieved, score, metric, run_id`. The golden dataset + scored results behind the CI gate.

Indexes: an ANN index (HNSW or IVFFlat) on each `embedding`, a `tsvector` GIN index on `chunks.text` for BM25-style search, FKs throughout. _Why HNSW vs. IVFFlat is a real choice: HNSW = better recall/latency, more memory; benchmark both before committing._

## 5. Integration plan (how 14 modules become one app)

The composition pattern, top to bottom:

- **Router/supervisor as the spine.** A LangGraph router (Module 4) is the entry node; it later becomes the multi-agent supervisor (Module 7) dispatching to specialist **subgraphs** (retrieval, tools, memory). New capabilities = new subgraphs or nodes, not new apps. _Why: this is the single decision that keeps the project "one app", everything hangs off the graph._
- **Shared memory.** All subgraphs read/write the same `memories` table, so context persists across agents and turns rather than being siloed per-agent.
- **Unified tracing.** Every node wraps its work in a Langfuse span sharing one `run_id`; one request = one trace regardless of how many subgraphs/tools it touched. _Why: multi-agent is undebuggable without a single correlated trace._
- **Gateway as the universal model interface.** No component calls a provider directly, embeddings, classification, generation, and eval-judge calls all go through LiteLLM, which is therefore the one place to add routing, caching, and cost accounting.
- **Caching layer.** Semantic + exact-match cache lives at the gateway (Module 11) so every path benefits without per-call code changes.
- **Evals + guardrails as cross-cutting gates.** Guardrails (Module 10) wrap the request boundary and tool calls; evals (Module 8) gate changes in CI. Both apply to the whole graph, not one module.

Build order is the module order: each module extends the previous app state and must pass its checkpoint and be integrated before the next begins (PRD §2 pace rule).

## 6. What "optimized" means, concretely, per layer

Optimization is **only** valid if Module 8 evals confirm quality didn't drop below the gate. Tuned to a small-local cheap tier plus the Azure cloud brain:

- **Gateway / model routing:** send cheap, high-volume calls (intent classification, query rewriting, draft generation, light reranking) to **small local Ollama models**; route reasoning-heavy synthesis and the eval judge to the **Azure deployment**. _Optimized = lowest-capable-model-that-passes-evals per task, not "best model everywhere."_
- **Caching:** exact-match cache for identical prompts; **semantic** cache for near-duplicate questions (embedding similarity above a threshold). _Optimized = high hit-rate without ever returning a semantically-wrong cached answer; the threshold is an eval-tuned knob._
- **Retrieval:** right-size `k`, rerank only the shortlist (not the whole corpus), and cache embeddings so re-asking doesn't re-embed. _Optimized = highest retrieval quality (context precision/recall in Ragas) at the lowest token + compute cost._
- **Database / pgvector:** correct ANN index + parameters, pre-filter by metadata before vector search where possible. _Optimized = recall held high while query latency stays acceptable._
- **Orchestration:** prune unnecessary agent hops; don't invoke a subgraph the router can resolve directly. _Optimized = fewest model calls per correct answer, multi-agent only where it earns its latency._
- **Prompts (Module 13, DSPy):** MIPROv2 searches instructions + few-shot demos against the golden set. _Optimized = measured before/after improvement on the same eval gate, never a vibe._

**The invariant:** every "optimization" must show a cost or latency win **and** a non-regression on evals. An optimization you can't prove with the harness doesn't count.
