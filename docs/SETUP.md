# MNEMIX — Setup Guide

## Prerequisites

- Python 3.11+ (tested on 3.14.4)
- Windows 11 or Linux/macOS
- Groq API key (free — [console.groq.com](https://console.groq.com)) — required
- NVIDIA NIM API key (free — [build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys)) — optional, adds a fallback tier
- Gemini API key (free — [aistudio.google.com/apikey](https://aistudio.google.com/apikey)) — optional, adds a fallback tier
- Supabase project with PostgreSQL database (free tier is sufficient)

## Installation

```powershell
cd D:\WorkSpace\mnemix

# Create virtual environment
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

The first run will download the sentence-transformers model (`all-MiniLM-L6-v2`, ~90MB). Subsequent runs use the HuggingFace cache.

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```powershell
copy .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=gsk_your_key_here

# Optional — leave blank to skip these chain slots entirely
NVIDIA_API_KEY=
GEMINI_API_KEY=
```

All other values have working defaults. See [CONFIGURATION.md](CONFIGURATION.md) for the full reference.

## Running the Server

```powershell
# From D:\WorkSpace\mnemix
.\venv\Scripts\python -m uvicorn main:app
```

On first start, the server:
1. Connects to Supabase PostgreSQL (tables must already exist — run `python database.py` once)
2. Seeds 50 questions from `data/questions_seed.json`
3. Warms up the embedding model

Expected output:
```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

For development with auto-reload:
```powershell
.\venv\Scripts\python -m uvicorn main:app --reload
```

## Running the CLI

The CLI talks to the server over HTTP. Keep the server running in one terminal, use the CLI in another.

```powershell
# In a second terminal (server must be running)
.\venv\Scripts\python cli.py --help
```

Available commands:
```
ingest     Ingest a resume or AI conversation export
gaps       Show memory coverage gaps
profile    Show your memory profile
history    Show past interview sessions
interview  Run a full mock interview session
```

## Port Configuration

The CLI connects to `http://localhost:8000` by default (uvicorn's default port). If port 8000 is in use:

1. Start the server on a different port: `--port 8001`
2. Update `BASE_URL` in `cli.py`:
   ```python
   BASE_URL = "http://localhost:8001/api/v1"
   ```

## First Use: Ingest Your Data

```powershell
# Ingest your resume
.\venv\Scripts\python cli.py ingest --resume path\to\resume.pdf

# Ingest ChatGPT conversation history
.\venv\Scripts\python cli.py ingest --chatgpt path\to\chatgpt_export.zip

# Ingest Claude conversation history
.\venv\Scripts\python cli.py ingest --claude path\to\claude_export.zip

# Check what categories have enough stories
.\venv\Scripts\python cli.py gaps

# Run an interview
.\venv\Scripts\python cli.py interview --type behavioral
```

Ingestion runs as a background job. The CLI polls for status and shows a progress indicator. Expect 30–120 seconds for a large AI export.

## Creating the Database Tables

Tables are created once against Supabase PostgreSQL. Run this before starting the server for the first time:

```powershell
.\venv\Scripts\python database.py
# → Tables created successfully.
```

Then apply the SQL migrations in the Supabase SQL Editor (Dashboard → SQL Editor):

1. **`migrations/001_pgvector.sql`** — enables the `vector` extension, adds `embedding_vec` column, builds HNSW index. Requires the `vector` extension to be enabled first (Dashboard → Database → Extensions → toggle "vector").
2. **`migrations/002_rls.sql`** — enables Row Level Security on all tables.
3. **`migrations/003_multiuser.sql`** — adds `user_id` to `user_profile`, tightens RLS policies for per-user data isolation.

## Verifying the Setup

```powershell
# Health check
curl http://localhost:8000/api/v1/health
# → {"status":"ok","version":"0.1.0"}

# Check question bank loaded
curl http://localhost:8000/api/v1/interview/sessions
# → []
```

## Resetting the Database

To start fresh (wipes all memories and sessions), truncate the tables in Supabase:

```sql
-- Run in Supabase SQL Editor
TRUNCATE memories, interview_sessions, session_answers, ingestion_jobs, user_profile RESTART IDENTITY CASCADE;
-- Questions are preserved — re-seed with:
-- DELETE FROM questions; then restart the server
```

## Common Issues

**`ModuleNotFoundError: No module named 'sentence_transformers'`**
Run `pip install -r requirements.txt` inside the activated venv.

**`ValidationError` on startup**
Your `.env` is missing a required key. Check that `GROQ_API_KEY` and `DATABASE_URL` are set (`NVIDIA_API_KEY`/`GEMINI_API_KEY` are optional).

**CLI returns 401 Unauthorized**
All API endpoints require a Supabase JWT. For local development, set `DEBUG=true` in `.env` and add the header `Authorization: Bearer dev-local` to your requests. The web UI handles auth automatically; the CLI does not yet pass auth headers.

**CLI hangs during ingestion**
Ingestion uses background tasks that make multiple LLM calls. A large ChatGPT export can take 2–5 minutes. The CLI polls for up to 10 minutes before timing out.

**Port already in use**
```powershell
# Find the process using port 8000
netstat -ano | findstr :8000
# Kill it
taskkill /PID <PID> /F
```
If the process can't be killed (Windows quirk), use a different port.
