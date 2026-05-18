# MNEMIX UI Build — Task Checklist

## Phase 1 — Foundation (CSS + JS)

- [x] css/design-system.css — tokens, reset, typography, utilities
- [x] css/components.css — buttons, cards, inputs, badges, progress, tabs, spinner, toasts, modal, pill, table
- [x] css/layout.css — sidebar, app shell, stat cards, dropzone, grids, responsive
- [x] js/auth.js — Supabase client (meta tags), getToken, requireAuth, sendMagicLink, handleCallback, logout
- [x] js/api.js — all API calls with async auth headers (get, post, upload, poll helpers)
- [x] js/utils.js — toast, scoreColor, formatDate, timeAgo, categoryLabel, coverageColor
- [x] js/components.js — appBase() Alpine shared function (userEmail, userInitials, logout)

## Phase 2 — Auth + Shell

- [x] login.html — email input, magic link send, sent confirmation state
- [x] auth/callback.html — handles Supabase redirect, routes to dashboard or onboarding
- [x] dashboard.html — stats row, memory coverage chart, quick actions, recent sessions

## Phase 3 — Core Features

- [x] documents.html — source list, upload modal, job polling, ingestion detail panel
- [x] memory.html — Overview / Gaps / Browse tabs, inline gap answering, memory search
- [x] interview.html — setup → active session → evaluating states, full-screen session view
- [x] report.html — score header, dimension breakdown, per-question accordion, patterns, next plan

## Phase 4 — Supporting Pages

- [x] history.html — score over time chart, session list, filter bar
- [x] chat.html — chat layout, memory-aware messages, suggested prompts
- [x] settings.html — Account / Career Profile / Notifications / Billing tabs
- [x] onboarding.html — 5-step wizard (welcome → profile → resume → AI exports → done)

## Phase 5 — Marketing

- [x] index.html — landing page (hero, problem/solution, how it works, features, pricing, footer)

## Backend Additions (needed for UI)

- [x] core/auth.py — get_current_user dependency (Supabase JWT validation)
- [x] api/profile.py — GET/PUT /api/v1/profile
- [x] api/chat.py — POST /api/v1/chat (memory retrieval + LLM response)
- [x] config.py — add SUPABASE_URL, SUPABASE_ANON_KEY settings
- [x] .env.example — add Supabase vars
- [x] requirements.txt — add aiofiles
- [x] main.py — StaticFiles mount + new routers (profile, chat)
