# MNEMIX — CLI Guide

The CLI (`cli.py`) is the primary user interface for MNEMIX. It calls the FastAPI server over HTTP — the server must be running before any CLI command will work.

```powershell
# Start the server (Terminal 1)
.\venv\Scripts\python -m uvicorn main:app

# Run CLI commands (Terminal 2)
.\venv\Scripts\python cli.py <command>
```

---

## Global Notes

- All commands connect to `http://localhost:8000/api/v1` by default. If your server is on a different port, update `BASE_URL` in `cli.py`.
- The CLI uses `httpx.Client` with a 30-second request timeout.
- Output uses Rich for colored terminal formatting.

---

## `ingest`

Ingest a resume PDF or AI conversation export to extract memories.

```powershell
.\venv\Scripts\python cli.py ingest --resume path\to\resume.pdf
.\venv\Scripts\python cli.py ingest --chatgpt path\to\chatgpt_export.zip
.\venv\Scripts\python cli.py ingest --claude path\to\claude_export.zip
.\venv\Scripts\python cli.py ingest --claude path\to\claude_export.md
.\venv\Scripts\python cli.py ingest --claude path\to\claude_conversations\
```

At least one of `--resume`, `--chatgpt`, or `--claude` is required. Multiple flags can be combined:

```powershell
.\venv\Scripts\python cli.py ingest --resume resume.pdf --chatgpt chatgpt.zip
```

**Process:**
1. Uploads the file via multipart POST
2. Shows a spinner while polling job status
3. Prints the result: `"Resume ingested: 8 memories extracted"` or an error message

**Polling:** The CLI checks status every 2 seconds. Ingestion typically takes 30–120 seconds for a large AI export due to batched LLM calls.

**Supported input formats:**
- `--resume`: `.pdf` only
- `--chatgpt`: `.zip` (containing `conversations.json`) or `.json`
- `--claude`: `.zip` (containing `.md` files), a single `.md` file, or a directory of `.md` files

---

## `gaps`

Show which interview categories have insufficient memory coverage.

```powershell
.\venv\Scripts\python cli.py gaps
```

**Output example:**
```
          Memory Gaps (3 categories below minimum)
┌──────────────────────┬──────┬──────┬──────────┬─────────────────────────┐
│ Category             │ Have │ Need │ Priority │ Suggested Questions     │
├──────────────────────┼──────┼──────┼──────────┼─────────────────────────┤
│ leadership           │    1 │    3 │   HIGH   │ Tell me about a time... │
│ conflict_resolution  │    0 │    2 │   HIGH   │                         │
│ system_design        │    0 │    1 │   HIGH   │                         │
└──────────────────────┴──────┴──────┴──────────┴─────────────────────────┘
```

Priority colors: RED = high, YELLOW = medium, GREEN = low.

If all categories meet their minimum: `"No gaps detected — all categories have sufficient coverage."`

Use this command after ingestion to see which categories you still need stories for, and to guide what to add as manual memories.

---

## `profile`

Show your memory profile — total count, breakdown by category, and most-accessed memories.

```powershell
.\venv\Scripts\python cli.py profile
```

**Output:**
```
╭──────────────── MNEMIX — Memory Profile ────────────────╮
│ Total Memories: 45                                       │
╰──────────────────────────────────────────────────────────╯
Field: software_engineering  |  Seniority: mid

      Memories by Category
┌────────────────────────┬───────┐
│ Category               │ Count │
├────────────────────────┼───────┤
│ technical_achievement  │    12 │
│ leadership             │     8 │
│ failure_learning       │     5 │
│ ...                    │   ... │
└────────────────────────┴───────┘

Most-Accessed Memories:
  1. [technical_achievement] Led a Django to FastAPI migration...
  2. [leadership] Coordinated a cross-team feature launch...
  3. [debugging] Traced a memory leak in a background worker...
```

---

## `interview`

Run a full mock interview session.

```powershell
.\venv\Scripts\python cli.py interview --type behavioral
.\venv\Scripts\python cli.py interview --type technical
.\venv\Scripts\python cli.py interview --type mixed
```

`--type` (default: `mixed`): the question set to draw from.

**Session flow:**

1. An intro panel is displayed.
2. Questions are shown one at a time in Rich panels.
3. For each question:
   - Type your answer at the prompt
   - Press **Enter twice** (blank line) to submit
   - Press **Ctrl+C** to cancel the session
4. After all 8 questions, the CLI waits for the LLM evaluation (30–90 seconds).
5. The feedback report is displayed.

**Input example:**
```
Question 1 of 8  [Category: leadership]
─────────────────────────────────────────────
Tell me about a time you led a team through a critical production incident.

Your answer (press Enter twice to submit):
> In my previous role, we had a database outage on a Friday evening...
> ...the team stayed on until 2 AM and we restored service.
> 
[blank line — submitted]
```

**Feedback report example:**
```
╭──────────────── MNEMIX Interview Feedback ────────────────╮
│ Overall Score: 72/100                                      │
│                                                            │
│ ═══ MNEMIX INTERVIEW REPORT ═══                           │
│ OVERALL SCORE: 72/100                                      │
│ VERDICT: Strong technical specificity, weak on outcomes.  │
│ ...                                                        │
╰────────────────────────────────────────────────────────────╯

Per-Question Breakdown:
  Q1: Tell me about a time you led...
  Score: 81/100  |  Good story structure, but no numbers on outcome.
  Memory opportunity missed: You have a story about your API migration...
```

**Evaluation timeout:** The CLI polls for up to 10 minutes (120 attempts × 5s). If evaluation doesn't complete, it prints the raw response and exits.

---

## `history`

Show a table of all past interview sessions.

```powershell
.\venv\Scripts\python cli.py history
```

**Output:**
```
              Interview History
┌───┬───────────┬──────────┬───────────┬─────────────────────┬────────────┐
│ # │ Type      │ Status   │ Score     │ Started             │ ID (short) │
├───┼───────────┼──────────┼───────────┼─────────────────────┼────────────┤
│ 1 │ behavioral│ complete │  72/100   │ 2026-05-18 10:00    │ e5f6a7b8   │
│ 2 │ technical │ complete │  85/100   │ 2026-05-17 15:30    │ a1b2c3d4   │
│ 3 │ mixed     │ complete │  90/100   │ 2026-05-16 09:15    │ f7e8d9c0   │
└───┴───────────┴──────────┴───────────┴─────────────────────┴────────────┘
```

Status colors: GREEN = complete, YELLOW = in_progress, BLUE = evaluating.

If no sessions exist: `"No sessions yet. Run python cli.py interview to start one."`

---

## Common Workflows

### First-time setup

```powershell
# 1. Ingest your data
.\venv\Scripts\python cli.py ingest --resume resume.pdf
.\venv\Scripts\python cli.py ingest --chatgpt chatgpt_export.zip
.\venv\Scripts\python cli.py ingest --claude claude_export.zip

# 2. Check coverage
.\venv\Scripts\python cli.py gaps

# 3. View profile
.\venv\Scripts\python cli.py profile

# 4. Run interviews
.\venv\Scripts\python cli.py interview --type behavioral
.\venv\Scripts\python cli.py interview --type technical
```

### Practice loop

```powershell
# Run an interview
.\venv\Scripts\python cli.py interview --type mixed

# Review history and compare scores
.\venv\Scripts\python cli.py history

# Check gaps — did the interview reveal any?
.\venv\Scripts\python cli.py gaps
```

---

## CLI Architecture

The CLI is built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/).

All CLI commands use the **synchronous** `httpx.Client` (not async). Typer commands are sync functions, so there's no event loop conflict.

The `_client()` factory creates a fresh client per request with a 30-second timeout:

```python
BASE_URL = "http://localhost:8000/api/v1"

def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=30.0)
```

Ingestion polling uses `_poll_job()` which loops with a 2-second sleep until `status in ("complete", "failed")`.

Interview evaluation polling uses a direct loop in the `interview` command with a 5-second sleep and 120-attempt maximum.
