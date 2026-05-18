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

**Phase:** v0.1 — Web UI + CLI, Supabase-backed, single user
**Goal:** Prove the core value: personal memory makes interview answers better
**Status:** End-to-end flow working: ingest → interview → scored feedback report

**What this phase is NOT:**
- Not production ready
- Not multi-user (user_profile is a single row)
- Not deployed (runs locally on http://localhost:8000)
- No Redis or complex infrastructure

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
├── Segmenter (split conversations by topic/time)
├── Classifier (professional vs personal vs behavioral)
└── Extractor (LLM → structured memory objects)
        ↓
PERSONAL MEMORY ENGINE
├── Embeddings (sentence-transformers, local, free)
├── Storage (Supabase PostgreSQL — embeddings as BYTEA, future: pgvector)
├── Retrieval (cosine similarity search)
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
│   │   ├── store.py             ← Save/retrieve memories from PostgreSQL
│   │   ├── retriever.py         ← Semantic search against memories
│   │   └── gap_detector.py      ← Find missing interview categories
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
│   ├── ingest.py               ← POST /ingest/resume, /ingest/export
│   ├── memory.py               ← GET /memory/profile, /memory/gaps
│   ├── interview.py            ← POST /interview/start, /interview/answer
│   └── transcript.py           ← POST /transcript/submit
│
├── data/
│   └── questions_seed.json     ← 50 pre-seeded interview questions
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

**Task → Model → Provider → Cost/1M**

```python
# Classification (professional vs personal)
# Rule-based Python first (free)
# Groq for ambiguous cases only
CLASSIFY:       groq/llama-3.1-8b-instant    $0.05/M    651 tok/s

# Memory extraction from conversation segments
EXTRACT:        deepseek-v4-flash             $0.14/M    cache: $0.014/M
                via DeepSeek API directly

# GitHub/code extraction
CODE_EXTRACT:   deepseek-v4-flash             $0.14/M

# User profile synthesis (one-time per user)
PROFILE:        deepseek-v4-pro               $0.435/M   USE NOW (75% off until May 31)

# Behavioral question generation
Q_BEHAVIORAL:   groq/gpt-oss-20b              $0.13/M    886 tok/s FASTEST

# Technical question generation
Q_TECHNICAL:    groq/qwen3-32b                $0.29/M    domain knowledge

# Behavioral + coding answer evaluation
EVAL:           deepseek-v4-pro               $0.435/M   reasoning quality

# System design evaluation (reasoning heavy)
EVAL_SYSDESIGN: deepseek-r1                   $0.55/M    best reasoning

# Feedback report generation (user-facing, quality critical)
FEEDBACK:       deepseek-v4-pro               $0.435/M   best writing

# Gap analysis (strategic reasoning)
GAP_ANALYSIS:   deepseek-r1                   $0.55/M

# Live interview assist (future — not in demo)
LIVE_ASSIST:    groq/gpt-oss-20b              $0.13/M    886 tok/s

# Embeddings — LOCAL, no API call needed
EMBEDDINGS:     sentence-transformers         FREE       all-MiniLM-L6-v2
```

### API Clients Setup

```python
# Groq — using OpenAI SDK with different base_url
from openai import AsyncOpenAI
groq_client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# DeepSeek — using OpenAI SDK with different base_url
deepseek_client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

# OpenRouter — fallback for everything
openrouter_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)
```

### Free Tier Status
```
Groq:     No credit card needed. 14,400 req/day free. Permanent.
DeepSeek: No credit card needed. 5M tokens free on signup. 30-day validity.
          USE THESE FREE TOKENS NOW during demo build.
          After 30 days: requires top-up payment.
OpenRouter: Free tier for some models. Backup/fallback only.
```

---

## DATABASE SCHEMA (Supabase PostgreSQL)

```sql
-- Supabase PostgreSQL — run `python database.py` to create tables

CREATE TABLE IF NOT EXISTS memories (
    id          TEXT PRIMARY KEY,
    content     TEXT NOT NULL,
    category    TEXT NOT NULL,
    themes      TEXT,               -- JSON array stored as text
    interview_qs TEXT,              -- JSON array stored as text
    confidence  REAL DEFAULT 0.0,
    source      TEXT,               -- resume/chatgpt/claude/manual
    date_context TEXT,
    has_outcome BOOLEAN DEFAULT FALSE,
    outcome_quantified BOOLEAN DEFAULT FALSE,
    embedding   BYTEA,              -- numpy array serialized
    created_at  TEXT DEFAULT (datetime('now')),
    access_count INTEGER DEFAULT 0,
    last_accessed TEXT
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id          TEXT PRIMARY KEY,
    started_at  TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    session_type TEXT,
    overall_score REAL,
    status      TEXT DEFAULT 'in_progress'
);

CREATE TABLE IF NOT EXISTS session_answers (
    id          TEXT PRIMARY KEY,
    session_id  TEXT REFERENCES interview_sessions(id),
    question_id TEXT,
    question_text TEXT,
    answer_text TEXT,
    answer_order INTEGER,
    memory_match_score REAL,
    specificity_score REAL,
    outcome_stated BOOLEAN DEFAULT FALSE,
    outcome_quantified BOOLEAN DEFAULT FALSE,
    memory_opportunity TEXT,
    total_score REAL,
    feedback_text TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS questions (
    id          TEXT PRIMARY KEY,
    text        TEXT NOT NULL,
    category    TEXT,
    field       TEXT,
    seniority   TEXT,
    source      TEXT DEFAULT 'seeded',
    effectiveness_score REAL DEFAULT 0.5,
    use_count   INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id          TEXT PRIMARY KEY,
    source_type TEXT,
    status      TEXT DEFAULT 'pending',
    total_segments INTEGER DEFAULT 0,
    processed   INTEGER DEFAULT 0,
    memories_found INTEGER DEFAULT 0,
    started_at  TEXT,
    completed_at TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS user_profile (
    id          INTEGER PRIMARY KEY DEFAULT 1,
    field       TEXT DEFAULT 'software_engineering',
    seniority   TEXT DEFAULT 'mid',
    primary_stack TEXT,             -- JSON array
    target_roles TEXT,              -- JSON array
    communication_style TEXT,       -- JSON object
    strength_areas TEXT,            -- JSON array
    gap_areas TEXT,                 -- JSON array
    career_narrative TEXT,
    last_updated TEXT DEFAULT (datetime('now'))
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

`.env` file structure (all required):

```env
# Groq (free, no credit card)
GROQ_API_KEY=gsk_...
GROQ_BASE_URL=https://api.groq.com/openai/v1

# DeepSeek (5M free tokens, no credit card)
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# OpenRouter (fallback)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Models (do not change without updating router.py)
MODEL_CLASSIFY=llama-3.1-8b-instant
MODEL_EXTRACT=deepseek-v4-flash
MODEL_PROFILE=deepseek-v4-pro
MODEL_Q_BEHAVIORAL=gpt-oss-20b
MODEL_Q_TECHNICAL=qwen3-32b
MODEL_EVAL=deepseek-v4-pro
MODEL_EVAL_SYSDESIGN=deepseek-r1
MODEL_FEEDBACK=deepseek-v4-pro
MODEL_GAP_ANALYSIS=deepseek-r1

# Database (Supabase PostgreSQL — password URL-encoded)
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# App settings
DEBUG=true
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
14. core/memory/retriever.py
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
24. main.py                ← FastAPI app wiring
25. cli.py                 ← Typer terminal interface

Phase 6: Test
─────────────────────────────────────────────────
26. End-to-end test: resume → memories → interview → feedback
```

---

## DEPENDENCIES (requirements.txt)

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
typer[all]==0.12.5
rich==13.9.0
pydantic==2.9.2
python-dotenv==1.0.1
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
pymupdf==1.24.13
sentence-transformers==3.3.1
openai==1.54.3
httpx==0.27.2
python-multipart==0.0.12
tiktoken==0.8.0
numpy==2.1.3
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

Decision: No authentication for demo
Reason:   Single user (Parth). Adding auth adds a week of work for zero value.
          Add Supabase Auth in v0.2 when sharing with friends.

Decision: Anonymize before any LLM call
Reason:   No PII in prompts. Reduces privacy risk to near zero.
          Also means Chinese models (DeepSeek, Groq) are safe to use.

Decision: Silent evaluation (not real-time feedback)
Reason:   Parth's explicit requirement. Evaluation after all answers, not during.
          More natural interview simulation. Avoids interrupting flow.

Decision: Pre-generate all 8 questions before interview starts
Reason:   Core latency strategy. 5-second wait upfront vs 3-second wait per question.
          Total wait is similar but perceived flow is much better.
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
- Embeddings stored as BYTEA (serialized numpy float32 array)
- Similarity search uses in-memory numpy cosine — future: pgvector operators
- SSL required; asyncpg connect_args uses ssl.CERT_NONE (Supabase self-signed CA)

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
❌ Never store Supabase credentials in source code — use meta tags in HTML, .env for backend
```

---

## CURRENT SPRINT

**Sprint: Demo v0.1**
**Status: Starting**
**First file to build: config.py**

Start here:
```
Build config.py → test it loads .env correctly
Then database.py → test it creates all tables
Then models/schemas.py → no testing needed, just schemas
Then llm/router.py → test with a simple call to Groq
```

**Success criteria for demo:**
1. Parth can run `python cli.py ingest --resume resume.pdf`
   and see memories extracted to terminal
2. Parth can run `python cli.py interview`
   and complete a full 8-question session
3. Feedback report is specific to his real projects (not generic)
4. Total demo cost stays under ₹50

---

*MNEMIX CLAUDE.md — v1.0 — May 2026*
*This file is the single source of truth for Claude Code.*
*Update this file when architectural decisions change.*