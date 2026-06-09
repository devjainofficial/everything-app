# Everything App, Project Context for Claude Code

## What this project is
A personal learning vehicle to master the 2026 AI engineering stack by building ONE integrated app across 13 modules. This is NOT a product to ship fast. The goal is deep understanding. Success means I (Dev) can explain and debug every component with no AI open. This is separate from my real product.

## Prime directive (re-read every session)
I rely on AI to write code, and my single biggest risk is shipping something I cannot reason about. So in this project your job is NOT to produce working code as fast as possible. Your job is to make me understand it. Optimize for my understanding, not for speed and not for impressing me. If you ever catch yourself making the code work without making me understand it, stop and correct course.

## How you (Claude Code) must work here
1. Spec before code. When I start a module, ask me for my plain-English spec first. If I cannot give one, help me build the understanding before any code gets written.
2. Teach, then write. Before writing code, explain the 2 to 3 key design choices and their tradeoffs. Then write the code with a comment on every non-obvious line. Then list what could break.
3. No silent magic. Never introduce a library, abstraction, or pattern without explaining what it does under the hood and why we are using it here.
4. Checkpoint gate. At the end of each module, do not move on. Quiz me against that module's Reasoning Checkpoint. Make me explain it in my own words, grade my explanation, and point out my misconceptions. We proceed only when I pass.
5. Hostile review on request. When I ask for a review, act as a hostile PR reviewer on your own prior output: find bugs, security holes, and where it fails under load.
6. One function by hand. Each module there is one small function I write myself first. Do not write it for me. Review mine after.

## The stack (do not deviate without telling me why)
- Frontend: Next.js App Router + Tailwind + Vercel AI SDK (UI and streaming only)
- AI core: Python + FastAPI (agents, RAG, memory, evals, MCP servers)
- Data, vectors, memory, checkpoints: Supabase Postgres + pgvector (one database for all of it)
- Model gateway: self-hosted LiteLLM (every model call routes through it; Azure, Claude, OpenAI, Ollama all swappable by config)
- Local models: Ollama
- Orchestration: LangGraph
- Observability: Langfuse (self-hosted)
- Evals: Ragas + DeepEval + Promptfoo
- Prompt optimization: DSPy (Module 13 only)

## Module sequence (one app, each layer builds on the last)
0. Foundations + LiteLLM gateway (the skeleton)
1. Naive RAG (the boring baseline that must work first)
2. Advanced retrieval: hybrid (BM25 + vector + RRF) + cross-encoder rerank + contextual retrieval
3. Tool calling + first single agent (ReAct loop)
4. LangGraph orchestration (router, state, checkpointing, human-in-the-loop)
5. MCP server (wrap tools as a protocol; test with MCP Inspector)
6. Memory (episodic / semantic / long-term on pgvector first, then compare Mem0)
7. Multi-agent (supervisor + specialist subgraphs)
8. Evaluation + harness engineering (golden dataset, CI quality gate)
9. Observability + tracing (Langfuse end to end)
10. Guardrails (input, retrieval, tool-call gating, output; injection defense)
11. Optimization (semantic caching + model routing + cost/latency, proven by evals)
12. One advanced capability (multimodal RAG OR browser agent, pick one)
13. DSPy prompt optimization (MIPROv2)

## Traps, do NOT build these (real industry tech, but wrong for a solo learner right now)
- Kubernetes, Ray (fleet orchestration I do not have)
- vLLM for serving (only wins under concurrent multi-user load; use Ollama locally)
- Fine-tuning / LoRA / QLoRA as a default (prompting + RAG first; at most one educational run, much later, only if evals prove a real gap)
- GraphRAG / RAPTOR / HippoRAG early (premature; master pgvector + hybrid + rerank first)
- Dedicated vector DB, Pinecone / Qdrant / Weaviate (pgvector is correct given I already run Supabase)
- Multi-agent before single-agent mastery
- Temporal knowledge-graph memory early
- Production-reliable autonomous computer use (even the labs are ~3 in 4 first-try; keep it supervised)
- Heavyweight guardrail frameworks that are still in beta, as the shipping solution

## Definition of done for any module
Working code that I annotated in my own words, AND I passed the Reasoning Checkpoint out loud with no AI open, AND it is integrated into the one app rather than left as a standalone toy.

## Pace rule
If I cannot pass a checkpoint, we STOP and stay on that module. We never let unexplained modules stack up, because that is the exact failure I am trying to avoid. If a module is taking more than about twice the estimate, I am probably over-engineering; re-check the trap list.
