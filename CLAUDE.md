# MNEMIX — Claude Code Context File
# Read this fully before writing any code.
# Last updated: May 2026

---

## PRODUCT IDENTITY

**Name:** MNEMIX
**Tagline:** "Your interview answers, in your voice, from your real experience."
**One line:** Memory-powered AI interview system for software, product, and data engineers.

**The core insight:**
Every AI interview tool (ParakeetAI, LockedIn AI, Final Round AI) generates generic
answers from a resume. MNEMIX generates authentic answers from 2 years of the user's
actual AI conversation history — ChatGPT exports, Claude exports, GitHub repos,
real project stories. The answers sound like the user because they ARE the user.

**North star:** Minimum latency. Maximum personalization. Both simultaneously.

---

## FOUNDER CONTEXT

**Founder:** Parth Jetani — solo full-stack developer, India
**Stack experience:** FastAPI, Django, Supabase, PostgreSQL, Redis, React/Next.js,
                     LLM APIs (Claude, Gemini, OpenAI), Docker, Celery
**Past products:**
- Dynbo: SMS marketing SaaS (Google App Engine, Python, Django) — BluHat Ventures
- StepGuide: Workflow SaaS (Google App Engine) — BluHat Ventures
- Veda: WhatsApp AI health coaching bot (FastAPI + Supabase + Gemini)
- Cliplift: Video SaaS (Next.js 15 + FastAPI + Supabase + Stripe/Razorpay + Apify)
- MNEMIX: This product (in progress)

**OS:** Windows 11
**Python:** 3.14.4
**Working directory:** mnemix/

---

## CURRENT BUILD PHASE

**Phase:** v0.1 — Web UI + CLI, Supabase-backed, multi-user
**Goal:** Prove the core value: personal memory makes interview answers better
**Status:** End-to-end flow working. Sharing with friends.

**What is complete:**
- Full ingestion → memory → interview → feedback pipeline
- Web UI (10 pages, Supabase magic link auth)
- pgvector similarity search (HNSW index, process-stateless)
- Multi-user data isolation (Supabase JWT + RLS on all tables)
- Rate limiting, anonymisation, structured logging

**What this phase is NOT:**
- Not production ready (single server, no horizontal scale)
- Not deployed (runs locally on http://localhost:8000)
- No Redis, Celery, or billing

---

## SYSTEM ARCHITECTURE

```
User Documents (Resume PDF + ChatGPT/Claude ZIP exports)
        ↓
INGESTION LAYER
├── Resume Parser (PyMuPDF — local, free)
├── ChatGPT Parser (conversations.json)
├── Claude Parser (markdown files)
└── Gemini Parser (Google Takeout JSON)
        ↓
PROCESSING PIPELINE
├── Segmenter (split conversations by topic)
├── Classifier (professional vs personal vs behavioral)
└── Extractor (LLM → structured memory objects)
        ↓
PERSONAL MEMORY ENGINE
├── Embeddings (sentence-transformers, local, free)
├── Storage (Supabase PostgreSQL — dual-write BYTEA + vector(384))
├── Retrieval (pgvector <=> cosine distance, HNSW index, per-user scoped)
└── Gap Detector (which interview categories are missing?)
        ↓
INTERVIEW ENGINE
├── Question Bank (50 seeded + learned from transcripts)
├── Session Manager (present questions one by one)
├── Silent Evaluator (collect answers, evaluate after session)
└── Feedback Generator (structured report after all answers)
        ↓
SELF-IMPROVEMENT ENGINE (background)
├── Transcript Processor (user submits real interview transcripts)
├── Question Effectiveness Tracker (which questions surface good stories?)
└── Cross-user Learning (better defaults for new users)
        ↓
TERMINAL INTERFACE (Typer CLI)
+ FastAPI (API-first, UI-ready for v0.2)
```

---

## PROJECT FILE STRUCTURE

```
mnemix/
├── CLAUDE.md               ← THIS FILE
├── .env                    ← API keys (never commit)
├── .env.example            ← Template (safe to commit)
├── main.py                 ← FastAPI app entry point
├── cli.py                  ← Typer terminal interface
├── config.py               ← All settings, loaded from .env
├── database.py             ← PostgreSQL connection + table creation
├── requirements.txt
│
├── llm/
│   ├── __init__.py
│   ├── router.py           ← Model selection by task
│   ├── prompts.py          ← ALL system prompts (single source of truth)
│   └── embeddings.py       ← Local sentence-transformers wrapper
│
├── core/
│   ├── __init__.py
│   ├── auth.py              ← Supabase JWT validation dependency
│   ├── user_context.py      ← UserContext dataclass + get_user_context dependency
│   ├── rate_limit.py        ← slowapi limiter (per-IP)
│   ├── logging_config.py    ← structured JSON logging + Sentry hook
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── resume_parser.py     ← PyMuPDF PDF → structured JSON
│   │   ├── chatgpt_parser.py    ← conversations.json → segments
│   │   ├── claude_parser.py     ← markdown files → segments
│   │   └── gemini_parser.py     ← Google Takeout JSON → segments
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── segmenter.py         ← Split by topic shift + time gap
│   │   ├── classifier.py        ← Rule-based + Groq for ambiguous
│   │   └── extractor.py         ← DeepSeek V4 Flash → memory objects
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── store.py                  ← Save/retrieve memories from PostgreSQL
│   │   ├── retriever.py              ← DEPRECATED (numpy, kept for rollback only)
│   │   ├── retriever_pgvector.py     ← Active retriever — pgvector SQL search
│   │   └── gap_detector.py           ← Find missing interview categories
│   │
│   └── interview/
│       ├── __init__.py
│       ├── session.py           ← Session state management
│       ├── question_bank.py     ← Load + select questions
│       ├── evaluator.py         ← Score answers silently
│       └── feedback.py          ← Generate feedback report
│
├── models/
│   ├── __init__.py
│   └── schemas.py              ← All Pydantic models
│
├── api/
│   ├── __init__.py
│   ├── ingest.py               ← POST /ingest/resume, /ingest/ai-export
│   ├── memory.py               ← GET /memory/profile, /memory/gaps, /memory/search
│   ├── interview.py            ← POST /interview/start, /interview/answer
│   ├── profile.py              ← GET/PUT /profile
│   └── chat.py                 ← POST /chat
│
├── data/
│   └── questions_seed.json     ← 50 pre-seeded interview questions
│
├── migrations/
│   ├── 001_pgvector.sql        ← vector extension + embedding_vec + HNSW index
│   ├── 002_rls.sql             ← Row Level Security on all tables
│   └── 003_multiuser.sql       ← user_id on user_profile + tightened RLS policies
│
├── frontend/                   ← Static web UI (served by FastAPI StaticFiles)
│   ├── index.html              ← Public landing page
│   ├── login.html              ← Supabase magic link sign-in
│   ├── onboarding.html         ← First-run 5-step setup wizard
│   ├── dashboard.html          ← Home screen
│   ├── interview.html          ← Interview session flow
│   ├── report.html             ← Post-interview feedback report
│   ├── memory.html             ← Memory browser + gap analysis
│   ├── documents.html          ← Upload resume / AI exports
│   ├── chat.html               ← Conversational memory search
│   ├── history.html            ← Past sessions list
│   ├── settings.html           ← User profile settings
│   ├── auth/callback.html      ← Supabase auth callback handler
│   ├── css/
│   │   ├── design-system.css   ← CSS variables, base reset
│   │   ├── components.css      ← Buttons, cards, inputs, toasts
│   │   └── layout.css          ← Sidebar, topbar, page shell
│   └── js/
│       ├── auth.js             ← Supabase auth wrapper (Auth object)
│       ├── api.js              ← All fetch() calls to backend (API object)
│       ├── utils.js            ← Shared helpers
│       └── components.js       ← Alpine.js component factories
│
└── tests/
    ├── test_parsers.py
    └── test_interview.py
```

---

## TECHNOLOGY STACK

### Core Framework
```
FastAPI          — async API framework
Typer            — terminal CLI (rich output)
Rich             — beautiful terminal formatting
Supabase PostgreSQL — database (asyncpg for async)
SQLAlchemy       — ORM (async mode)
Pydantic v2      — data validation
PyMuPDF (fitz)   — PDF parsing (local, free)
sentence-transformers — embeddings (local, free, no API cost)
  model: all-MiniLM-L6-v2 (384-dim, fast, good enough for demo)
python-dotenv    — .env loading
httpx            — async HTTP client
```

### AI Models (ALL via OpenAI-compatible SDK)

**Task → Model → Provider**

Each task routes through an ordered provider chain (see `TASK_CHAINS` in `llm/router.py`), not a single provider. Chain slots with no API key configured are skipped without a network call.

```python
# Classification (professional vs personal)
# Rule-based Python first (free). LLM only for ambiguous cases.
CLASSIFY:       Groq llama-3.1-8b-instant → Gemini gemma-4-31b-it → NIM meta/llama-3.1-8b-instruct

# Memory extraction from conversation segments
EXTRACT:        NIM deepseek-ai/deepseek-v4-flash → Gemini gemini-3.5-flash-lite → Groq llama-3.3-70b-versatile

# Behavioral + coding answer evaluation
EVAL:           NIM moonshotai/kimi-k2-thinking → Groq llama-3.3-70b-versatile

# System design evaluation (reasoning heavy)
EVAL_SYSDESIGN: NIM moonshotai/kimi-k2-thinking → Groq qwen/qwen3-32b

# Feedback report generation (user-facing)
FEEDBACK:       NIM moonshotai/kimi-k2-thinking → Gemini gemini-3.5-flash-lite → Groq llama-3.3-70b-versatile

# Gap analysis
GAP_ANALYSIS:   Groq qwen/qwen3-32b → NIM meta/llama-3.1-8b-instruct

# Embeddings — LOCAL, no API call
EMBEDDINGS:     all-MiniLM-L6-v2           sentence-transformers (free)
```

### API Clients Setup

```python
# Three OpenAI-compatible clients — no single "primary" provider, each task has its own chain
from openai import AsyncOpenAI
groq_client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)
nvidia_client = AsyncOpenAI(api_key=settings.NVIDIA_API_KEY or "unset", base_url=settings.NVIDIA_BASE_URL)
gemini_client = AsyncOpenAI(api_key=settings.GEMINI_API_KEY or "unset", base_url=settings.GEMINI_BASE_URL)
```

### Free Tier Status
```
Groq:   No credit card needed. 8B-class models: 14,400 req/day. llama-3.3-70b-versatile: ~1,000 req/day.
NVIDIA: NIM free tier via build.nvidia.com. Optional — chain slots skip cleanly if NVIDIA_API_KEY unset.
Gemini: Free tier via aistudio.google.com. Optional — chain slots skip cleanly if GEMINI_API_KEY unset.
```

### Quota Tracking

`llm/router.py` has an in-process `QuotaTracker` per (provider, model): an RPM sliding window (60s) plus an RPD daily counter with date-rollover. `LLMRouter.call()` walks a task's chain, skips any slot whose tracker reports exhausted, and on a live `RateLimitError` marks that slot exhausted for the rest of the day (respecting `Retry-After`, capped at 5s) before falling through to the next slot in the chain. This state is in-process only — correct for the current single-process local deployment, not for multi-worker/multi-pod (would need a Redis-backed counter to scale out).

---

## DATABASE SCHEMA (Supabase PostgreSQL)

```sql
-- Core tables created by `python database.py` (idempotent).
-- Then apply migrations/ in order via Supabase SQL Editor:
--   001_pgvector.sql → 002_rls.sql → 003_multiuser.sql

CREATE TABLE IF NOT EXISTS memories (
    id               TEXT PRIMARY KEY,
    user_id          TEXT,                   -- Supabase user UUID (multi-user)
    content          TEXT NOT NULL,
    category         TEXT NOT NULL,
    themes           TEXT,                   -- JSON array as text
    interview_qs     TEXT,                   -- JSON array as text
    confidence       REAL DEFAULT 0.0,
    source           TEXT,                   -- resume/chatgpt/claude/manual
    date_context     TEXT,
    has_outcome      BOOLEAN DEFAULT FALSE,
    outcome_quantified BOOLEAN DEFAULT FALSE,
    embedding        BYTEA,                  -- legacy numpy blob (kept for rollback)
    embedding_vec    vector(384),            -- pgvector column (active retriever)
    created_at       TEXT,
    access_count     INTEGER DEFAULT 0,
    last_accessed    TEXT
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT,                   -- Supabase user UUID
    started_at      TEXT,
    completed_at    TEXT,
    session_type    TEXT,
    overall_score   REAL,
    status          TEXT DEFAULT 'in_progress',
    questions_list  TEXT,                   -- JSON array of {id,text,category}
    feedback_report TEXT                    -- full LLM report text
);

CREATE TABLE IF NOT EXISTS session_answers (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT REFERENCES interview_sessions(id),
    question_id         TEXT,
    question_text       TEXT,
    answer_text         TEXT,
    answer_order        INTEGER,
    memory_match_score  REAL,
    specificity_score   REAL,
    outcome_stated      BOOLEAN DEFAULT FALSE,
    outcome_quantified  BOOLEAN DEFAULT FALSE,
    coherence_score     REAL,
    memory_opportunity  TEXT,
    total_score         REAL,
    feedback_text       TEXT,
    created_at          TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id                  TEXT PRIMARY KEY,
    text                TEXT NOT NULL,
    category            TEXT,
    field               TEXT,
    seniority           TEXT,
    source              TEXT DEFAULT 'seeded',
    effectiveness_score REAL DEFAULT 0.5,
    use_count           INTEGER DEFAULT 0,
    created_at          TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id              TEXT PRIMARY KEY,
    user_id         TEXT,                   -- Supabase user UUID
    source_type     TEXT,
    status          TEXT DEFAULT 'pending',
    progress        INTEGER DEFAULT 0,
    total_segments  INTEGER DEFAULT 0,
    processed       INTEGER DEFAULT 0,
    memories_found  INTEGER DEFAULT 0,
    created_at      TEXT,
    started_at      TEXT,
    completed_at    TEXT,
    error_message   TEXT
);

CREATE TABLE IF NOT EXISTS user_profile (
    id               INTEGER PRIMARY KEY,   -- auto-increment
    user_id          TEXT UNIQUE,           -- Supabase user UUID (one row per user)
    field            TEXT DEFAULT 'software_engineering',
    seniority        TEXT DEFAULT 'mid',
    primary_stack    TEXT,                  -- JSON array
    target_roles     TEXT,                  -- JSON array
    communication_style TEXT,              -- JSON object
    strength_areas   TEXT,                  -- JSON array
    gap_areas        TEXT,                  -- JSON array
    career_narrative TEXT,
    last_updated     TEXT
);
```

---

## MEMORY CATEGORIES

These are the exact category strings used throughout the system:

```python
MEMORY_CATEGORIES = [
    # Behavioral
    "leadership",
    "conflict_resolution",
    "failure_learning",
    "technical_achievement",
    "collaboration",
    "ambiguity_handling",
    "initiative",
    "communication",
    "pressure_handling",

    # Technical
    "system_design",
    "debugging",
    "tech_decisions",
    "performance_optimization",
    "architecture",

    # Identity
    "career_goal",
    "value",
    "strength",
    "working_style",
    "self_awareness"
]

REQUIRED_CATEGORIES = {
    "leadership":           {"minimum": 3, "weight": "high"},
    "conflict_resolution":  {"minimum": 2, "weight": "high"},
    "failure_learning":     {"minimum": 2, "weight": "high"},
    "technical_achievement":{"minimum": 3, "weight": "high"},
    "collaboration":        {"minimum": 2, "weight": "medium"},
    "ambiguity_handling":   {"minimum": 2, "weight": "medium"},
    "initiative":           {"minimum": 2, "weight": "medium"},
    "system_design":        {"minimum": 1, "weight": "high"},
    "debugging":            {"minimum": 2, "weight": "medium"},
    "tech_decisions":       {"minimum": 2, "weight": "high"},
    "career_goal":          {"minimum": 1, "weight": "medium"},
    "value":                {"minimum": 1, "weight": "low"},
    "strength":             {"minimum": 2, "weight": "medium"},
}
```

---

## CLASSIFICATION RULES

Rule-based classifier — no LLM call needed for these:

```python
# Auto-ACCEPT (professional content)
PROFESSIONAL_KEYWORDS = [
    "api", "database", "bug", "error", "deploy", "code", "server",
    "architecture", "client", "sprint", "deadline", "code review",
    "production", "migration", "performance", "system", "endpoint",
    "backend", "frontend", "pipeline", "infrastructure", "kubernetes",
    "docker", "redis", "postgresql", "fastapi", "django", "react",
    "debugging", "refactor", "pull request", "merge", "release",
    "stakeholder", "product manager", "team lead", "manager",
    "requirement", "specification", "roadmap", "feature", "sprint"
]

# Auto-REJECT (personal content)
PERSONAL_KEYWORDS = [
    "recipe", "movie", "fitness", "workout", "diet", "weight",
    "relationship", "girlfriend", "boyfriend", "wife", "husband",
    "family", "mom", "dad", "sister", "brother", "travel", "vacation",
    "birthday", "medical", "doctor", "health symptom", "religion",
    "politics", "game", "sports score", "music playlist", "netflix",
    "amazon prime", "book recommendation", "restaurant", "food"
]

# Send to Groq Llama (ambiguous — needs LLM)
AMBIGUOUS_SIGNALS = [
    "i tend to", "i've realized", "i struggle with",
    "my manager", "at work", "in my career", "i feel",
    "i'm thinking about", "communication", "leadership style"
]
```

---

## CODING STANDARDS

Follow these exactly — no exceptions:

### Python Style
```python
# Always async FastAPI endpoints
@router.post("/endpoint")
async def my_endpoint(data: MySchema) -> ResponseSchema:
    ...

# Always validate with Pydantic v2
class MySchema(BaseModel):
    field: str
    optional_field: Optional[str] = None

# Always structured error responses
raise HTTPException(
    status_code=400,
    detail={"error": "description", "code": "ERROR_CODE"}
)

# HTTP status codes:
# 200 — success
# 400 — bad input / validation error
# 404 — not found
# 422 — Pydantic validation error (automatic)
# 500 — server/LLM error

# Environment variables via config.py — NEVER hardcoded
from config import settings
api_key = settings.GROQ_API_KEY  # correct
api_key = "gsk_abc123"           # NEVER do this
```

### LLM Calls
```python
# Always use the router — never call LLM clients directly in core/
from llm.router import llm_router
result = await llm_router.call(task="extract", prompt=my_prompt)

# Always handle LLM errors gracefully
try:
    result = await llm_router.call(task="extract", prompt=prompt)
except LLMError as e:
    # log, return partial result, or raise HTTP 500
    raise HTTPException(status_code=500, detail={"error": str(e)})

# Always parse JSON responses safely
import json
try:
    parsed = json.loads(result)
except json.JSONDecodeError:
    # try to extract JSON from markdown fences
    clean = result.strip().strip("```json").strip("```").strip()
    parsed = json.loads(clean)
```

### Database
```python
# Always use async SQLAlchemy
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def my_function(db: AsyncSession = Depends(get_db)):
    ...

# Always use parameterized queries — never string interpolation
# Correct:
result = await db.execute(
    select(Memory).where(Memory.user_id == user_id)
)
# Never:
result = await db.execute(f"SELECT * FROM memories WHERE user_id = '{user_id}'")
```

### File Naming
```
snake_case for all Python files
snake_case for all variables and functions
PascalCase for Pydantic models and classes
UPPER_CASE for constants
```

---

## LLM PROMPTS — KEY ONES

All prompts live in `llm/prompts.py`. Never define prompts inline in core modules.

### Classification Prompt (Groq Llama)
```
Purpose: Classify a conversation segment
Input: user_messages (string)
Output: {"category": "PROFESSIONAL|BEHAVIORAL_PROFESSIONAL|PERSONAL|MIXED",
         "confidence": 0.0-1.0}
Max tokens: 50 (just the JSON)
```

### Memory Extraction Prompt (DeepSeek V4 Flash)
```
Purpose: Extract structured memories from professional content
Input: user_messages, field, role
Output: {"memories": [{content, category, themes, interview_qs,
                       confidence, has_outcome, outcome_quantified}]}
Max tokens: 1000
CRITICAL: Extract from USER messages only, never AI responses
CRITICAL: Minimum confidence 0.65 to include
CRITICAL: Return {"memories": []} if nothing qualifies
```

### Evaluation Prompt (DeepSeek V4 Pro)
```
Purpose: Score an interview answer silently
Input: question, answer, top_memories, field, seniority
Output: {memory_match: 0-3, specificity: 0-3,
         outcome_stated: bool, outcome_quantified: bool,
         memory_opportunity_missed: uuid|null,
         coherence: 0-2, specific_feedback: string}
Max tokens: 300
```

### Feedback Prompt (DeepSeek V4 Pro)
```
Purpose: Generate post-session feedback report
Input: all evaluations, profile summary
Output: Structured text (not JSON) for terminal display
Tone: Direct, honest, like a respected mentor
Max tokens: 1500
```

---

## TERMINAL INTERFACE FLOW

```
$ python cli.py

╔══════════════════════════════════════╗
║         MNEMIX v0.1 Demo            ║
║   Memory-Powered Interview Coach    ║
╚══════════════════════════════════════╝

Commands:
  ingest    — Upload resume or AI export history
  gaps      — Show memory gaps + fill them
  interview — Start a mock interview session
  profile   — View your memory profile
  history   — View past sessions

$ python cli.py ingest --resume path/to/resume.pdf
$ python cli.py ingest --chatgpt path/to/chatgpt_export.zip
$ python cli.py ingest --claude path/to/claude_export.zip
$ python cli.py gaps
$ python cli.py interview --type behavioral
$ python cli.py interview --type technical
$ python cli.py interview --type mixed
$ python cli.py profile
```

### Interview Terminal Flow
```
[MNEMIX] Starting behavioral interview session...
[MNEMIX] Loading your memory profile...
[MNEMIX] Pre-generating questions (this takes ~5 seconds)...
[MNEMIX] Ready. 8 questions. Silent evaluation. Report at end.

─────────────────────────────────────────
Question 1/8
─────────────────────────────────────────
Tell me about the most technically challenging
problem you solved in the last 12 months.

Take your time. Type your answer below.
Press Enter twice when finished.
─────────────────────────────────────────
> [user types answer]
> [blank line to submit]

[MNEMIX] Got it. Next question in 3 seconds...

[after all 8 questions]

[MNEMIX] Evaluating your responses...
[MNEMIX] Generating feedback report...

[full feedback report printed to terminal]
```

---

## LATENCY STRATEGY

### Pre-Generation (Most Important)
```python
# When user runs `python cli.py interview`:
# BEFORE showing first question:
# 1. Load user profile into RAM
# 2. Select 8 questions
# 3. Generate ALL 8 questions simultaneously (asyncio.gather)
# 4. Cache results in memory dict
# 5. Show first question from cache → instant

# Between questions: 3-second countdown (feels natural, not rushed)
# All questions already ready → no wait between them
```

### Parallel LLM Calls
```python
# Never sequential when parallel is possible
# Wrong (slow):
for question in questions:
    result = await generate_question(question)

# Right (fast):
tasks = [generate_question(q) for q in questions]
results = await asyncio.gather(*tasks)
```

### Embedding
```python
# sentence-transformers runs locally
# No API call = no network latency
# Cache embeddings — never re-embed the same text twice
```

---

## DATA PRIVACY RULES

These are non-negotiable. Follow them exactly:

```
1. NEVER send user's name, email, phone, LinkedIn URL, GitHub 
   username, or company name to any external API.

2. ONLY send anonymized professional context:
   - Project descriptions (no company names)
   - Technical decisions made
   - Skills demonstrated
   - Career stories (anonymized)

3. Raw AI exports: process in Python → extract memories → 
   raw file content NEVER sent to external APIs.

4. The LLM only sees extracted segments, never full export files.

5. Embeddings run locally — sentence-transformers — 
   zero external calls for embedding generation.
```

---

## ENVIRONMENT VARIABLES

`.env` file structure:

```env
# Groq — required (free, no credit card)
GROQ_API_KEY=gsk_...

# NVIDIA NIM — optional, adds a fallback tier to several chains
NVIDIA_API_KEY=

# Gemini (OpenAI-compat) — optional, adds a fallback tier to several chains
GEMINI_API_KEY=

# Models — Groq tier (change via .env, not in code)
MODEL_CLASSIFY=llama-3.1-8b-instant
MODEL_EXTRACT=llama-3.3-70b-versatile
MODEL_EVAL=llama-3.3-70b-versatile
MODEL_EVAL_SYSDESIGN=qwen/qwen3-32b
MODEL_FEEDBACK=llama-3.3-70b-versatile
MODEL_GAP_ANALYSIS=qwen/qwen3-32b

# Models — NVIDIA NIM tier
MODEL_NIM_CLASSIFY=meta/llama-3.1-8b-instruct
MODEL_NIM_EXTRACT=deepseek-ai/deepseek-v4-flash
MODEL_NIM_REASONING=moonshotai/kimi-k2-thinking

# Models — Gemini tier
MODEL_GEMINI_FLASH_LITE=gemini-3.5-flash-lite
MODEL_GEMMA4=gemma-4-31b-it

# Database (Supabase PostgreSQL — password URL-encoded, REQUIRED)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR-PASSWORD@db.YOUR-PROJECT.supabase.co:5432/postgres

# Supabase (required for web UI auth)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# App settings
DEBUG=false
LOG_LEVEL=INFO
MAX_MEMORIES_PER_USER=500
MIN_CONFIDENCE_THRESHOLD=0.65
INTERVIEW_QUESTIONS_COUNT=8
```

---

## BUILD ORDER (Follow Exactly)

Build one file at a time. Test each before moving on.

```
Phase 1: Foundation
─────────────────────────────────────────────────
1.  config.py              ← Load all env vars
2.  database.py            ← PostgreSQL setup + create tables
3.  models/schemas.py      ← All Pydantic schemas
4.  llm/router.py          ← Model routing logic
5.  llm/prompts.py         ← All prompts (strings only)
6.  llm/embeddings.py      ← sentence-transformers wrapper

Phase 2: Ingestion
─────────────────────────────────────────────────
7.  core/ingestion/resume_parser.py
8.  core/ingestion/chatgpt_parser.py
9.  core/ingestion/claude_parser.py
10. core/processing/segmenter.py
11. core/processing/classifier.py
12. core/processing/extractor.py

Phase 3: Memory
─────────────────────────────────────────────────
13. core/memory/store.py
14. core/memory/retriever_pgvector.py   ← active (retriever.py kept for rollback)
15. core/memory/gap_detector.py

Phase 4: Interview
─────────────────────────────────────────────────
16. data/questions_seed.json   ← 50 seeded questions
17. core/interview/question_bank.py
18. core/interview/session.py
19. core/interview/evaluator.py
20. core/interview/feedback.py

Phase 5: Interface
─────────────────────────────────────────────────
21. api/ingest.py
22. api/memory.py
23. api/interview.py
24. api/profile.py
25. api/chat.py
26. main.py                ← FastAPI app wiring
27. cli.py                 ← Typer terminal interface
28. frontend/              ← Static web UI (10 pages)

Phase 6: Test
─────────────────────────────────────────────────
29. End-to-end test: resume → memories → interview → feedback
```

---

## DEPENDENCIES (requirements.txt)

See `requirements.txt` for pinned versions. Key packages:

```
fastapi, uvicorn[standard]     — async API + server
typer[all], rich               — CLI
pydantic, pydantic-settings    — validation + config
sqlalchemy[asyncio], asyncpg   — async ORM + PostgreSQL driver
pgvector                       — vector type for SQLAlchemy
slowapi                        — rate limiting
pymupdf                        — PDF parsing
sentence-transformers          — local embeddings
openai                         — OpenAI-compatible SDK (Groq + NVIDIA NIM + Gemini)
httpx                          — async HTTP client (CLI + auth)
python-multipart               — file upload parsing
numpy                          — embedding math
```

---

## KEY DECISIONS LOG

These decisions were made deliberately. Do not change without reason.

```
Decision: Supabase PostgreSQL (migrated from SQLite)
Reason:   Already using Supabase for auth — same project, no extra infra.
          Eliminates SQLite locking issues entirely. WAL/retry workarounds removed.

Decision: sentence-transformers for embeddings (not OpenAI)
Reason:   Free, local, no API cost, no latency. 384-dim is enough for demo.
          Switch to OpenAI text-embedding-3-small for production.

Decision: Groq for classification and question generation
Reason:   886 tokens/second. Speed critical for pre-generation.
          Free tier covers all demo usage.

Decision: DeepSeek V4 Flash for extraction
Reason:   $0.14/M with prompt caching at $0.014/M. Best cost for volume task.
          5M free tokens covers entire demo phase.

Decision: DeepSeek V4 Pro for evaluation and feedback (USE NOW)
Reason:   75% promo price until May 31, 2026. $0.435/M instead of $1.74/M.
          Quality needed for user-facing feedback. Use while cheap.

Decision: DeepSeek R1 for gap analysis and system design eval
Reason:   Best reasoning model at its price point. Beats Sonnet at 1/10th cost.

Decision: Terminal first, UI second
Reason:   Fastest path to testing core value. UI adds weeks, terminal adds days.
          FastAPI is API-first so UI can be added without changing backend.

Decision: Supabase JWT auth + multi-user isolation
Reason:   Sharing with friends required data isolation. get_user_context FastAPI
          dependency validates JWT and threads user_id through every DB call.
          RLS on all tables provides defence-in-depth via PostgREST as well.

Decision: Anonymize before any LLM call
Reason:   No PII in prompts. Reduces privacy risk to near zero.
          Also means Chinese models (DeepSeek, Groq) are safe to use.

Decision: Silent evaluation (not real-time feedback)
Reason:   Parth's explicit requirement. Evaluation after all answers, not during.
          More natural interview simulation. Avoids interrupting flow.

Decision: Pre-generate all 8 questions before interview starts
Reason:   Core latency strategy. 5-second wait upfront vs 3-second wait per question.
          Total wait is similar but perceived flow is much better.

Decision: Multi-provider TASK_CHAINS router (Groq + NVIDIA NIM + Gemini), OpenRouter removed
Reason:   MODEL_CLASSIFY was pinned to llama-3.3-70b-versatile (~1,000 req/day on Groq
          free tier) despite classify running on every raw segment — the highest-volume
          task. Fixed by moving classify to llama-3.1-8b-instant (14,400 req/day) and,
          more broadly, replacing the single Groq-primary/OpenRouter-fallback router with
          per-task provider chains so no one task is single-point-of-failure on one
          free-tier cap. NVIDIA_API_KEY/GEMINI_API_KEY are optional — a chain slot with
          no key configured is skipped without a network call, so this degrades cleanly
          to Groq-only if those keys are never added.

Decision: Removed PROFILE / Q_BEHAVIORAL / Q_TECHNICAL task chains, prompts, and model config
Reason:   Audit found these were never invoked anywhere in the codebase — profile is plain
          manual CRUD (api/profile.py, no LLM synthesis), and interview questions come
          entirely from the static seeded question bank (core/interview/question_bank.py,
          no LLM generation). Removed the dead TASK_CHAINS entries from llm/router.py, the
          unused PROFILE_PROMPT/Q_BEHAVIORAL_PROMPT/Q_TECHNICAL_PROMPT from llm/prompts.py,
          and the corresponding MODEL_PROFILE/MODEL_Q_BEHAVIORAL/MODEL_Q_TECHNICAL/
          MODEL_NIM_PROFILE/MODEL_NIM_CODER settings from config.py and .env(.example).
          If AI-generated questions or AI profile synthesis becomes a real feature later,
          reintroduce these deliberately rather than leaving them as unwired scaffolding.
```

---

## KNOWN CONSTRAINTS

```
Windows 11 specific:
- Use pathlib.Path() for all file paths (not os.path string concatenation)
- Use forward slashes or Path() objects
- PowerShell terminal (not bash)

Python 3.14.4:
- All modern async features available
- Use asyncio.TaskGroup for parallel tasks (Python 3.11+)

PostgreSQL / Supabase:
- Embeddings dual-written: BYTEA (legacy, rollback) + vector(384) (active, pgvector)
- Similarity search: pgvector <=> cosine distance operator, HNSW index
- SSL required; asyncpg connect_args uses ssl.CERT_NONE (Supabase self-signed CA)
- RLS enabled on all 6 tables. Backend bypasses via postgres superuser connection.

sentence-transformers first load:
- Downloads model (~90MB) on first run
- Subsequent runs use cached model
- Expect 30-60 second first-run delay for embedding init
```

---

## WHAT TO NEVER DO

```
❌ Never send raw file content to any LLM API
❌ Never hardcode API keys anywhere (use .env only)
❌ Never use synchronous I/O in async functions (use aiofiles or asyncio)
❌ Never define prompts inline in core/ modules (use llm/prompts.py)
❌ Never call LLM clients directly in core/ (use llm/router.py)
❌ Never skip error handling on LLM calls (they fail occasionally)
❌ Never store PII (name, email, phone) in the database
❌ Never use string formatting for SQL queries
❌ Never add Redis/Celery (out of scope for v0.1)
❌ Never store Supabase credentials in source code — use /config.js endpoint for frontend, .env for backend
```

---

## CURRENT SPRINT

**Sprint: Friend Beta**
**Status: Ready to share**

**Completed this sprint:**
- pgvector similarity search (migrations/001_pgvector.sql applied)
- Multi-user data isolation (JWT auth + RLS)
- Security hardening (rate limiting, anonymisation, RLS policies)
- Full doc update (all 11 docs/ files + README + CLAUDE.md)

**Next actions:**
1. Parth ingests his real resume + ChatGPT/Claude exports
2. Share with 2–3 friends for feedback on answer quality
3. Tune extraction and evaluation prompts based on real data quality
4. Decide on deployment (Render / Railway / fly.io) if sharing beyond local

---

*MNEMIX CLAUDE.md — v1.1 — May 2026*
*This file is the single source of truth for Claude Code.*
*Update this file when architectural decisions change.*