# MNEMIX

**Memory-powered AI interview coach. Your answers, in your voice, from your real experience.**

Most interview tools generate generic answers from a resume. MNEMIX generates authentic answers from your actual AI conversation history — two years of ChatGPT and Claude exports, real project stories, decisions you actually made. The feedback is specific because the memories are real.

---

## How It Works

```
Your resume + AI chat exports
          ↓
  Extract professional memories
  (local embeddings, no cloud storage)
          ↓
  Run a mock interview (8 questions)
          ↓
  Get scored feedback tied to your real stories
```

MNEMIX ingests your documents, classifies and extracts professional memories, then conducts a personalized mock interview. Each answer is evaluated against your memory bank — you get scored on how well you used your real experience, not just how fluent the answer sounded.

---

## Quickstart

**Prerequisites:** Python 3.11+, a [Groq API key](https://console.groq.com) (free), an [OpenRouter API key](https://openrouter.ai) (free).

```powershell
# 1. Clone and install
git clone <repo>
cd mnemix
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configure
copy .env.example .env
# Edit .env: add GROQ_API_KEY and OPENROUTER_API_KEY

# 3. Start the server (Terminal 1)
.\venv\Scripts\python -m uvicorn main:app

# 4. Ingest your data (Terminal 2)
.\venv\Scripts\python cli.py ingest --resume resume.pdf
.\venv\Scripts\python cli.py ingest --chatgpt chatgpt_export.zip
.\venv\Scripts\python cli.py ingest --claude claude_export.zip

# 5. Run an interview
.\venv\Scripts\python cli.py interview --type behavioral
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `cli.py ingest --resume FILE` | Extract memories from a resume PDF |
| `cli.py ingest --chatgpt FILE` | Extract memories from a ChatGPT export |
| `cli.py ingest --claude FILE` | Extract memories from a Claude export |
| `cli.py gaps` | Show which interview categories need more stories |
| `cli.py profile` | View total memories and category breakdown |
| `cli.py interview --type behavioral\|technical\|mixed` | Run a mock interview |
| `cli.py history` | View past sessions and scores |

---

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + uvicorn |
| CLI | Typer + Rich |
| Database | SQLite + aiosqlite + SQLAlchemy 2.0 async |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, free) |
| LLM (primary) | Groq — `llama-3.3-70b-versatile`, `qwen3-32b`, `gpt-oss-20b` |
| LLM (fallback) | OpenRouter free tier |
| Similarity search | NumPy vectorized cosine similarity |

All LLM calls go through a single router (`llm/router.py`). Embeddings run locally — no text is sent to external APIs for embedding.

---

## Scoring

Each interview answer is scored across five dimensions:

| Dimension | Range | What It Measures |
|-----------|-------|-----------------|
| Memory match | 0–3 | How specifically the answer references real experiences from your memory bank |
| Specificity | 0–3 | Level of concrete detail: technologies, project context, numbers |
| Outcome stated | 0 or 2 | Whether the answer described what resulted |
| Outcome quantified | 0 or 1 | Whether the outcome included measurable numbers |
| Coherence | 0–2 | Answer structure and clarity |

**Total score:** `(memory_match + specificity + outcome_stated_pts + outcome_quantified_pts + coherence) / 11 × 100`

---

## Privacy

- Resume PII (email, phone, URLs) is stripped before any LLM call.
- AI export contents are processed locally — only extracted segments are sent to the LLM, never raw files.
- The extraction prompt instructs the model to replace company names with generic descriptions.
- Embeddings run on your machine via sentence-transformers. Zero external calls for embedding.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Installation, configuration, running the server |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | All `.env` variables with descriptions and defaults |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview, data flow, module relationships |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | All FastAPI endpoints with request/response examples |
| [docs/CLI_GUIDE.md](docs/CLI_GUIDE.md) | All CLI commands with examples and output |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | All 6 tables, columns, types, and relationships |
| [docs/LLM_SYSTEM.md](docs/LLM_SYSTEM.md) | Router, task routing, prompts, fallback strategy |
| [docs/INGESTION_PIPELINE.md](docs/INGESTION_PIPELINE.md) | Parsers, segmenter, classifier, extractor |
| [docs/MEMORY_SYSTEM.md](docs/MEMORY_SYSTEM.md) | Store, retriever, gap detector |
| [docs/INTERVIEW_ENGINE.md](docs/INTERVIEW_ENGINE.md) | Question bank, session, evaluator, feedback generator |

---

## Project Status

v0.1 — terminal-only demo, single user, local machine. Full end-to-end flow verified.

Next: ingest real data, tune prompts based on real evaluation quality, build web UI.
