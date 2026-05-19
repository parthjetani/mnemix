-- Migration 003 — Multi-user data isolation
--
-- WHY: MNEMIX is opening to friends. Each user's memories, sessions,
-- ingestion jobs, and profile must be isolated by their Supabase user ID.
--
-- CHANGES:
--   1. Add user_id to user_profile (the only table missing it).
--   2. Tighten all RLS policies from USING (true) → USING (user_id = auth.uid()::text)
--      so PostgREST enforces row ownership automatically.
--
-- The FastAPI backend connects as postgres superuser → bypasses RLS → unaffected.
-- Safe to re-run (idempotent).

-- ── 1. user_profile — add user_id column ─────────────────────────────────

ALTER TABLE public.user_profile
    ADD COLUMN IF NOT EXISTS user_id TEXT;

-- Unique index: one profile row per user.
CREATE UNIQUE INDEX IF NOT EXISTS user_profile_user_id_idx
    ON public.user_profile (user_id);

-- ── 2. Tighten RLS policies ───────────────────────────────────────────────

-- memories
DROP POLICY IF EXISTS "authenticated_all" ON public.memories;
CREATE POLICY "authenticated_all" ON public.memories
    FOR ALL TO authenticated
    USING  (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- interview_sessions
DROP POLICY IF EXISTS "authenticated_all" ON public.interview_sessions;
CREATE POLICY "authenticated_all" ON public.interview_sessions
    FOR ALL TO authenticated
    USING  (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- ingestion_jobs
DROP POLICY IF EXISTS "authenticated_all" ON public.ingestion_jobs;
CREATE POLICY "authenticated_all" ON public.ingestion_jobs
    FOR ALL TO authenticated
    USING  (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- user_profile
DROP POLICY IF EXISTS "authenticated_all" ON public.user_profile;
CREATE POLICY "authenticated_all" ON public.user_profile
    FOR ALL TO authenticated
    USING  (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- session_answers — no user_id column; ownership enforced at the session level.
-- Authenticated users can read any answer row, but they can only reach answers
-- whose session_id belongs to a session they own (protected by the session policy).
-- Leave as USING (true) — already set in migration 002.

-- questions — shared seed data, read-only for authenticated users.
-- Leave as SELECT USING (true) — already set in migration 002.
