# Everything App, Product Requirements Document (PRD)

> **Type:** Learning project, not a commercial product. No real users, no revenue, no go-to-market.
> **Single user:** Dev. **Core success metric:** learning depth, the ability to explain and debug every component with no AI open.
> Source of truth for stack, modules, and constraints: `CLAUDE.md`. This PRD does not override it; it operationalizes it.

---

## 1. Purpose & learning objectives

Build **one** integrated AI application across 13 modules (0–13) for the sole purpose of mastering the 2026 AI engineering stack. The app is the vehicle; understanding is the product.

By the end, Dev should be able to:

- Draw the full request flow (UI → gateway → agent → data → back) on a whiteboard from memory.
- Explain, for every module, *what it does under the hood, why it exists, and what breaks it*, with no AI open.
- Open any module's code and debug a live failure (bad retrieval, a stuck graph, a failing eval, a runaway cost) by reasoning, not by pasting it into a model.
- Produce a short teach-back (written or recorded) per module. The act of teaching is the proof of understanding.

**Prime directive (inherited):** optimize for Dev's understanding, never for speed or for impressiveness. Code that works but isn't understood is a failure condition, not a win.

## 2. The user and the end-state bar

There is exactly one user: Dev. He can read and trace code fluently but currently relies on AI to write most of it. The explicit goal is to close that gap. Therefore scope is deliberately small and deep: each module is a thin, well-understood slice, not a feature-complete subsystem.

**"Done" for the whole app** = all modules 0–13 integrated into a single running app **AND** Dev can explain/debug any of them live with no AI **AND** each module has a teach-back artifact proving he can teach it.

**"Done" for a single module** (inherited, non-negotiable): working code annotated by Dev in his own words **AND** the module's Reasoning Checkpoint passed out loud with no AI open **AND** it is wired into the one app, not left as a standalone toy.

**Pace:** relaxed, no deadline. The checkpoint gate is the only pace control. If a checkpoint can't be passed, work stops and stays on that module. Unexplained modules are never allowed to stack up. If a module runs past ~2× its mental estimate, that's the signal to re-check the trap list for over-engineering.

## 3. Scope (the 13 modules as the feature set)

Each module is one capability. The corpus the app reasons over is **technical papers + framework documentation Dev is studying** (PDF-heavy). Constraints that shape everything below: **solo dev, capable reasoning runs on a company Azure OpenAI deployment called through the LiteLLM gateway (the default brain for the reasoning-heavy modules: agent, orchestration, multi-agent, guardrail reasoning, DSPy), local Ollama small models as the cheap tier (classification, query rewriting, drafts, light tasks), every model call routed through the gateway so no single provider is a hard dependency.**

> Format per module: **Definition of Done (DoD)** = the inherited 3-part gate, specialized. **Reasoning Checkpoint (RC)** = the questions Dev must answer out loud, no AI, to pass.

### Module 0. Foundations + LiteLLM gateway (the skeleton)
**DoD:** A FastAPI service and Next.js shell talk to each other; every model call goes through a self-hosted LiteLLM gateway with at least one local (Ollama) model and the Azure OpenAI deployment (or any cloud model), all swappable by config alone.
**RC:** Why does *every* call route through a gateway instead of calling providers directly? What exactly does the gateway abstract, and what would break if you bypassed it for "just one" call? How would you swap the default model with zero code changes?

### Module 1. Naive RAG (the boring baseline that must work first)
**DoD:** Ingest a few papers, chunk, embed into pgvector, retrieve top-k by cosine similarity, stuff into a prompt, answer with citations.
**RC:** Walk a question from text to answer: where do embeddings come from, what does the vector index actually compare, and why is top-k cosine a *weak* baseline? Name two failure modes you'd expect on technical PDFs.

### Module 2. Advanced retrieval (hybrid + rerank + contextual)
**DoD:** BM25 + vector retrieval fused with RRF, then a cross-encoder rerank, plus contextual retrieval (chunk-level context added at index time). Demonstrably beats Module 1 on your own questions.
**RC:** Why does combining BM25 and vectors beat either alone? What does RRF do that naive score-averaging doesn't? What's the difference between the *retriever* and the *reranker*, and why run both?

### Module 3. Tool calling + first single agent (ReAct loop)
**DoD:** One agent that can call tools (e.g. retrieval, a calculator) in a reason→act→observe loop and decide when to stop.
**RC:** What is the model actually emitting when it "calls a tool"? Who executes the tool, the model or your code? Draw the ReAct loop and point to where an infinite loop could form.

### Module 4. LangGraph orchestration (router, state, checkpointing, human-in-the-loop)
**DoD:** The agent runs as a LangGraph graph with explicit state, a router node, persisted checkpoints, and at least one human-in-the-loop interrupt.
**RC:** What is "state" in the graph and why make it explicit instead of hidden in Python variables? What does a checkpoint save, and how does it let you pause/resume? Where does the human interrupt fit and what does it protect against?

### Module 5. MCP server (wrap tools as a protocol)
**DoD:** Your tools are exposed via an MCP server and verified with MCP Inspector; the agent consumes them over the protocol.
**RC:** What problem does MCP solve that a plain function call doesn't? What's the contract between an MCP server and a client? Why might you wrap a tool you already have as MCP?

### Module 6. Memory (episodic / semantic / long-term)
**DoD:** Memory layered on pgvector first (episodic, semantic, long-term), then a deliberate comparison against Mem0.
**RC:** Define episodic vs. semantic vs. long-term memory in this app's terms. How is "memory" different from "retrieval over documents"? What did Mem0 give you that your pgvector version didn't, and was it worth a dependency?

### Module 7. Multi-agent (supervisor + specialist subgraphs)
**DoD:** A supervisor dispatches to specialist subgraphs (e.g. a retrieval specialist, a tool specialist); only attempted after single-agent mastery.
**RC:** What does the supervisor decide, and on what signal? When does multi-agent actually help vs. just add latency and failure surface? How does shared state flow between subgraphs?

### Module 8. Evaluation + harness engineering
**DoD:** A golden dataset plus a harness (Ragas + DeepEval + Promptfoo) that runs as a CI quality gate and can fail a change.
**RC:** What does each tool measure that the others don't? What makes a *golden* dataset trustworthy? How does an eval gate change the way you'd make a risky change to retrieval?

### Module 9. Observability + tracing (Langfuse end to end)
**DoD:** Every request produces an end-to-end trace in self-hosted Langfuse: spans for retrieval, model calls, tools, cost, and latency.
**RC:** What is a span vs. a trace? Given a slow or wrong answer, how do you use the trace to localize the cause? What can a trace tell you that an eval score can't?

### Module 10. Guardrails (input, retrieval, tool-call gating, output; injection defense)
**DoD:** Guardrails at four points (input, retrieval, tool-call gating, output), including a prompt-injection defense, using lightweight (non-beta-framework) components.
**RC:** Name the four gate points and what each one catches. Walk through how a prompt-injection payload hidden in a retrieved document would try to hijack the agent, and where your gates stop it.

### Module 11. Optimization (semantic caching + model routing + cost/latency, proven by evals)
**DoD:** Semantic caching and model routing that measurably cut cost/latency **without** dropping eval scores below the Module 8 gate. Route cheap paths (classification, query rewriting, drafts) to small local Ollama models, and reasoning-heavy synthesis to the Azure deployment, then prove what routing actually buys.
**RC:** How does semantic caching differ from exact-match caching, and when does it return a wrong answer? On what features do you route a request to a cheap vs. expensive model? How do you *prove* an optimization didn't quietly degrade quality?

### Module 12. One advanced capability (multimodal RAG OR browser agent)
**DoD:** One advanced capability integrated into the app. *Choice deferred:* both paths documented; pick when you arrive (heavy reasoning routed to the Azure deployment, light steps local).
**RC (multimodal):** How do image/figure embeddings differ from text, and how do you retrieve across both? **RC (browser):** Why must this stay supervised, and where would an unsupervised step fail? Either way: why was this the right *single* advanced capability to add, and what did you consciously *not* build?

### Module 13. DSPy prompt optimization (MIPROv2)
**DoD:** A prompt/program optimized with DSPy MIPROv2 against your golden dataset, with before/after eval numbers.
**RC:** What is DSPy optimizing (the weights, the prompt, or the program structure)? What does MIPROv2 search over? Why is this last, and why is it pointless without Module 8's evals already in place?

## 4. Non-goals & traps to skip

**Non-goals:** shipping fast; multi-user support, auth, or accounts; market personas, sizing, or business KPIs; production SLAs; impressing anyone. The audience is Dev's own understanding.

**Traps, do NOT build these** (inherited; real industry tech, wrong for a solo learner now):

- Kubernetes / Ray (fleet orchestration not needed).
- vLLM serving (only wins under concurrent multi-user load; use Ollama locally).
- Fine-tuning / LoRA / QLoRA as a default (prompting + RAG first; at most one educational run much later, *only* if evals prove a real gap).
- GraphRAG / RAPTOR / HippoRAG early (master pgvector + hybrid + rerank first).
- Dedicated vector DB (Pinecone/Qdrant/Weaviate), pgvector is correct given Supabase is already running.
- Multi-agent before single-agent mastery.
- Temporal knowledge-graph memory early.
- Production-reliable autonomous computer use (keep it supervised).
- Heavyweight, still-in-beta guardrail frameworks as the shipping solution.

## 5. Success criteria (understanding & debuggability, not business KPIs)

The project succeeds when:

1. **Explainability:** Dev can give the Reasoning Checkpoint answer for every module out loud, no AI open.
2. **Debuggability:** Given an injected failure in any module, Dev can localize and explain the cause using the code, traces, and evals, without delegating the reasoning.
3. **Integration:** all modules run as *one* app, not 14 disconnected demos.
4. **Teachability:** a teach-back artifact exists per module; if Dev can teach it, he owns it.
5. **Honest scope:** the trap list stayed un-built; no module was "made to work" without being understood.

Explicitly **not** success criteria: latency benchmarks for their own sake, feature count, user numbers, revenue, or how impressive the app looks in a demo.
