-- db/schema.sql — Module 1 (naive RAG) data model on Postgres + pgvector.
-- Run once against the Supabase database. Safe to re-run (idempotent).

create extension if not exists vector;   -- pgvector: adds the `vector` column type + distance ops

-- ── documents: one row per source paper/PDF ──────────────────────────────────
create table if not exists documents (
    id          bigint generated always as identity primary key,
    title       text not null,                       -- human-readable name (shown in citations)
    source_uri  text,                                -- where it came from (file path / URL)
    created_at  timestamptz not null default now()
);

-- ── chunks: one row per chunk of a document ──────────────────────────────────
-- The embedding is THIS chunk's fingerprint; `text` is what we hand back as the citation.
create table if not exists chunks (
    id           bigint generated always as identity primary key,
    document_id  bigint not null references documents(id) on delete cascade,  -- delete doc -> its chunks go too
    ordinal      int  not null,                       -- chunk position in the document (0,1,2,...)
    text         text not null,                       -- the chunk's raw text
    embedding    vector(768),                         -- nomic-embed-text fingerprint (MUST be 768 dims)
    created_at   timestamptz not null default now()
);

-- ── ANN index for fast cosine search ─────────────────────────────────────────
-- vector_cosine_ops = compare by cosine distance (the `<=>` operator).
-- At small scale an exact scan is fine; HNSW keeps it fast as the corpus grows.
create index if not exists chunks_embedding_hnsw
    on chunks using hnsw (embedding vector_cosine_ops);

-- ── Module 2: full-text (keyword) search support ─────────────────────────────
-- A generated tsvector column (auto-maintained from `text`) is the "keyword" half
-- of hybrid search; the GIN index makes term matching fast. Fused with vector search
-- via RRF, it catches exact tokens (e.g. "RRF", "BM25") that embeddings can miss.
alter table chunks add column if not exists text_tsv tsvector
    generated always as (to_tsvector('english', text)) stored;

create index if not exists chunks_text_tsv_gin on chunks using gin (text_tsv);
