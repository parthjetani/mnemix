-- Migration 002 — Row Level Security on all public tables
--
-- WHY: Supabase exposes every public table via PostgREST. Without RLS, any
-- request using the anon key (including from a browser) can read or write
-- all rows directly, bypassing the FastAPI backend entirely.
--
-- EFFECT: enabling RLS with no permissive policies locks down PostgREST
-- completely. The FastAPI backend connects as the `postgres` superuser,
-- which bypasses RLS by default — zero application impact.
--
-- FUTURE (multi-user): replace the FOR ALL TO authenticated USING (true)
-- policies below with per-user policies:
--   USING (user_id = auth.uid()::text)
-- once user_id is populated from the Supabase JWT on every write.
--
-- Safe to re-run (all statements are idempotent).

-- ── Enable RLS ────────────────────────────────────────────────────────────

ALTER TABLE public.memories           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_answers    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingestion_jobs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profile       ENABLE ROW LEVEL SECURITY;

-- ── Policies ──────────────────────────────────────────────────────────────
--
-- v0.1 is single-user. These policies allow any authenticated Supabase
-- session to reach the data via PostgREST (e.g. future direct-client use).
-- Anon (unauthenticated) requests remain blocked.
--
-- Drop-and-recreate pattern keeps re-runs idempotent.

-- memories
DROP POLICY IF EXISTS "authenticated_all" ON public.memories;
CREATE POLICY "authenticated_all" ON public.memories
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- interview_sessions
DROP POLICY IF EXISTS "authenticated_all" ON public.interview_sessions;
CREATE POLICY "authenticated_all" ON public.interview_sessions
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- session_answers
DROP POLICY IF EXISTS "authenticated_all" ON public.session_answers;
CREATE POLICY "authenticated_all" ON public.session_answers
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- questions (read-only for authenticated; seeded by backend only)
DROP POLICY IF EXISTS "authenticated_read" ON public.questions;
CREATE POLICY "authenticated_read" ON public.questions
  FOR SELECT TO authenticated USING (true);

-- ingestion_jobs
DROP POLICY IF EXISTS "authenticated_all" ON public.ingestion_jobs;
CREATE POLICY "authenticated_all" ON public.ingestion_jobs
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- user_profile
DROP POLICY IF EXISTS "authenticated_all" ON public.user_profile;
CREATE POLICY "authenticated_all" ON public.user_profile
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
