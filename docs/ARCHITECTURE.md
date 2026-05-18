# MNEMIX — Architecture

MNEMIX is a memory-powered interview coaching system. It ingests a user's professional history (resume, AI conversation exports), extracts structured memories, and conducts personalized mock interviews where answers are evaluated against those memories.

## System Overview

```
User Documents
├── Resume PDF
├── ChatGPT export (.zip or .json)
└── Claude export (.zip, .md, or directory)
         │
         ▼
INGESTION LAYER (core/ingestion/)
├── resume_parser.py    — PyMuPDF text extraction + anonymization
├── chatgpt_parser.py   — conversations.json → message segments
└── claude_parser.py    — markdown files → message segments
         │
         ▼
PROCESSING PIPELINE (core/processing/)
├── segmenter.py    — split conversations by topic/time
├── classifier.py   — professional vs personal vs mixed
└── extractor.py    — LLM → MemoryCreate objects
         │
         ▼
PERSONAL MEMORY ENGINE (core/memory/)
├── store.py        — save/retrieve memories from SQLite
├── retriever.py    — in-memory cosine similarity search
└── gap_detector.py — identify missing interview categories
         │
         ▼
INTERVIEW ENGINE (core/interview/)
├── question_bank.py — load 50 seeded questions, select 8 per session
├── session.py       — session state, answer collection
├── evaluator.py     — score answers against retrieved memories
└── feedback.py      — generate structured feedback report
         │
         ▼
INTERFACE LAYER
├── api/ (FastAPI)   — HTTP API for all operations
└── cli.py (Typer)   — terminal interface, calls API over HTTP
```

## Architectural Principles

**API-first design.** The CLI calls the FastAPI server over HTTP. It never imports core modules directly. This keeps the backend independent and ready for a future web UI.

**LLM isolation.** All LLM calls go through `llm/router.py`. Core modules never import `openai` or call providers directly. All prompts live in `llm/prompts.py` — never inline in core modules.

**Local embeddings.** sentence-transformers (`all-MiniLM-L6-v2`) runs locally. No embedding API calls, no latency, no cost. Embeddings are cached in memory by text content.

**SQLite for demo.** All data persists in `mnemix.db`. The ORM schema mirrors a Supabase+pgvector production schema — switching is a connection string change plus replacing numpy similarity search with pgvector operators.

**Single-user model.** No authentication. `user_profile` table has a single row with `id=1`. All memories, sessions, and jobs belong to the one user running the system.

## Data Flow: Ingestion

```
1. POST /api/v1/ingest/resume   (or /ingest/ai-export)
2. File saved to tempfile
3. IngestionJob created (status=pending)
4. BackgroundTask launched → response returned immediately
5. Background task:
   a. parse file → raw segments (list of message strings)
   b. segment → group by topic/time
   c. classify each segment (professional / personal / mixed)
   d. extract memories from professional segments (LLM, batched)
   e. embed each memory (local sentence-transformers)
   f. save to SQLite + add to in-memory retriever index
   g. update IngestionJob (status=complete, memories_found=N)
6. CLI polls GET /ingest/status/{job_id} until complete
```

## Data Flow: Interview

```
1. POST /api/v1/interview/start
   → select_questions(): opener + gap questions + type-specific + wildcard
   → create_session(): save to DB with questions_list JSON
   → return first question

2. For each question: POST /api/v1/interview/answer
   → add_answer(): save to session_answers
   → get_next_question(): return next unanswered, or None

3. Last answer triggers:
   → complete_session(): set status=evaluating
   → BackgroundTask: _run_evaluation()
      a. evaluate_session(): for each answer in parallel:
         - embed answer → semantic search top-5 memories
         - call EVALUATION_PROMPT via LLM
         - parse scores (memory_match, specificity, outcome, coherence)
         - normalize to 0-100
      b. generate_feedback(): call FEEDBACK_PROMPT with all evaluations
      c. update session: status=complete, overall_score, feedback_report

4. CLI polls GET /interview/evaluate/{session_id}
   → returns {status: "evaluating"} until complete
   → returns FeedbackReport when done
```

## Module Dependencies

```
cli.py
  └── httpx → FastAPI (api/)

api/
  ├── ingest.py → core/ingestion/, core/processing/, core/memory/
  ├── memory.py → core/memory/
  └── interview.py → core/interview/

core/ (never imports from api/ or cli/)
  ├── ingestion/ → llm/router.py, llm/prompts.py
  ├── processing/ → llm/router.py, llm/prompts.py, llm/embeddings.py
  ├── memory/ → database.py, llm/router.py, llm/embeddings.py
  └── interview/ → core/memory/, llm/router.py, llm/prompts.py, llm/embeddings.py

llm/
  ├── router.py → openai SDK only (Groq + OpenRouter clients)
  ├── prompts.py → (no imports, string constants only)
  └── embeddings.py → sentence_transformers, numpy
```

## Key Files

| File | Role |
|------|------|
| `config.py` | All settings loaded from `.env`. Singleton `settings` object. |
| `database.py` | All 6 ORM tables + async engine + `get_db()` dependency + `async_session_factory` |
| `llm/router.py` | Central LLM gateway. Task → model + client routing. Groq primary, OpenRouter fallback. |
| `llm/prompts.py` | All 8 prompt templates. Single source of truth. |
| `llm/embeddings.py` | Lazy-loaded sentence-transformers. In-memory cache. |
| `core/processing/extractor.py` | Extracts structured MemoryCreate objects from segments. Quality determines all downstream personalization. |
| `core/interview/evaluator.py` | Scores answers against retrieved memories. Where the product's core value is demonstrated. |
| `data/questions_seed.json` | 50 pre-seeded interview questions across 18 categories. |
