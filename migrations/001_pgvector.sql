-- Migration 001 — pgvector for the memory retriever
--
-- Prereq: enable the `vector` extension on the Supabase project once. Either:
--   (a) Supabase dashboard → Database → Extensions → toggle "vector" on
--   (b) run as a superuser:  CREATE EXTENSION IF NOT EXISTS vector;
--
-- This script then plants the `embedding_vec` column, backfills it from the
-- existing BYTEA `embedding` column, and builds an HNSW index for cosine
-- similarity search. It is safe to run repeatedly (idempotent).
--
-- After applying, swap `memory_retriever` in main.py to import from
-- core.memory.retriever_pgvector instead of core.memory.retriever, then
-- delete the numpy retriever once the cutover is verified.

-- 1. Enable extension (no-op if already on).
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add the typed column. Skipped if it already exists.
ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS embedding_vec vector(384);

-- 3. Backfill from the BYTEA column. numpy float32 little-endian, 4 bytes/dim.
--    Only fills rows where the new column is still null, so re-runs are cheap.
UPDATE memories
SET embedding_vec = (
    SELECT ('[' || string_agg(
        (get_byte(embedding, off)
         | (get_byte(embedding, off + 1) << 8)
         | (get_byte(embedding, off + 2) << 16)
         | (get_byte(embedding, off + 3) << 24))::text,
        ','
    ) || ']')::vector
    FROM generate_series(0, 384 * 4 - 4, 4) AS off
)
WHERE embedding IS NOT NULL AND embedding_vec IS NULL;

-- 4. HNSW index for cosine similarity. Hard-coded params are pgvector defaults.
CREATE INDEX IF NOT EXISTS memories_embedding_vec_hnsw
    ON memories USING hnsw (embedding_vec vector_cosine_ops);
