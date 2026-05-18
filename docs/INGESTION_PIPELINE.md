# MNEMIX — Ingestion Pipeline

The ingestion pipeline transforms raw user documents into structured `MemoryCreate` objects stored in PostgreSQL.

## Pipeline Overview

```
Input file (PDF / ZIP / JSON / MD / directory)
        │
        ▼
Parser  (core/ingestion/)
  → raw segments: [{conversation_id, messages: [str], source, created_at}]
        │
        ▼
Segmenter  (core/processing/segmenter.py)
  → topic-cohesive segments
        │
        ▼
Classifier  (core/processing/classifier.py)
  → PROFESSIONAL / BEHAVIORAL_PRO / MIXED / PERSONAL
        │
  (PERSONAL discarded)
        │
        ▼
Extractor  (core/processing/extractor.py)
  → [MemoryCreate, ...]
        │
        ▼
Embedder  (llm/embeddings.py)
  → per-memory embedding vector
        │
        ▼
Store  (core/memory/store.py)
  → memories table in PostgreSQL
        │
        ▼
Retriever index update  (core/memory/retriever.py)
  → in-memory numpy matrix updated live
```

---

## Parsers

### Resume Parser (`core/ingestion/resume_parser.py`)

Extracts professional memories directly from a PDF resume.

**Input:** Path to a `.pdf` file

**Process:**
1. Opens the PDF with PyMuPDF (`fitz.open()`)
2. Extracts text from all pages (`page.get_text()`)
3. **Anonymizes** the text — strips emails, phone numbers, LinkedIn URLs, GitHub URLs, and generic URLs via regex
4. Calls `EXTRACTION_PROMPT` with the anonymized text
5. Parses the JSON response into `MemoryCreate` objects

**Output:** `{"raw_text_length": int, "raw_memories": list[MemoryCreate]}`

Anonymization happens before any LLM call. This is a hard privacy requirement — no PII is ever sent to external APIs.

---

### ChatGPT Parser (`core/ingestion/chatgpt_parser.py`)

Parses a ChatGPT conversation export.

**Input:** Path to a `.zip` file or `.json` file

**ZIP handling:** Finds `conversations.json` inside the archive.

**Format support:**
- **Current format** (`mapping` tree): ChatGPT exports a dict where each node has `{id, parent, children, message}`. The parser walks the tree to reconstruct message order.
- **Legacy format** (flat `messages` list): Direct list of `{author: {role}, content: {parts}}` objects.

**Extraction rules:**
- Only `message.author.role == "user"` messages are kept
- Messages shorter than 20 words are discarded
- Content is joined from `content.parts` (list of strings)

**Output:** `[{conversation_id, messages: [str], source: "chatgpt", created_at: str}]`

---

### Claude Parser (`core/ingestion/claude_parser.py`)

Parses a Claude conversation export.

**Input:** Path to a `.zip` file, a `.md` file, or a directory containing `.md` files.

**Format:** Claude exports conversations as Markdown files with `[Human]` / `[Assistant]` turn markers. Both `[Human]` and `Human:` prefix styles are handled.

**Extraction:** Human turns are split by regex, then the assistant reply following each turn is stripped. Turns shorter than 20 words are discarded.

**Output:** `[{conversation_id: filename_stem, messages: [str], source: "claude", created_at: None}]`

---

## Segmenter (`core/processing/segmenter.py`)

Splits a long conversation into topically coherent segments for classification and extraction.

**Input:** A single `{messages: [str], ...}` dict from a parser.

**Three-pass splitting (in priority order):**

1. **Phrase split** — If any message starts with a topic-shift phrase (`"anyway,"`, `"moving on"`, `"on a separate"`, `"changing topics"`, `"different question"`), split at that point. Applied first, cheapest.

2. **Embedding distance split** — If a sub-group has ≥5 messages, compute cosine similarity between consecutive pairs. Split where similarity drops below 0.70 (meaning the topics diverged). Applied only after phrase splitting, on groups large enough to justify the cost.

3. **Minimum length filter** — Any segment with fewer than 30 total words is discarded.

**Output:** List of segment dicts, each with a `segment_index` field added for traceability.

---

## Classifier (`core/processing/classifier.py`)

Classifies each segment into one of four categories: `PROFESSIONAL`, `BEHAVIORAL_PRO`, `MIXED`, or `PERSONAL`.

**Three-step logic:**

1. **Professional keyword match** (free): Joins all message text, lowercases, checks for any of 38 professional keywords (`api`, `database`, `deploy`, `production`, `sprint`, `redis`, `fastapi`, etc.). If found → `PROFESSIONAL`. No LLM call.

2. **Personal keyword match** (free): Checks for any of 28 personal keywords (`recipe`, `fitness`, `relationship`, `movie`, `travel`, etc.) with no professional keywords present. If found → `PERSONAL`. No LLM call.

3. **Groq LLM** (for ambiguous segments only): Calls `CLASSIFICATION_PROMPT` with max 50 tokens. Returns JSON with `category` and `confidence`.

**On LLM error:** Falls back to `PROFESSIONAL` to avoid discarding potentially valuable content.

The keyword lists are defined as module-level constants `PROFESSIONAL_KEYWORDS`, `PERSONAL_KEYWORDS`, and `AMBIGUOUS_SIGNALS` in `classifier.py`.

---

## Extractor (`core/processing/extractor.py`)

Extracts structured `MemoryCreate` objects from professional segments using an LLM.

### `extract_memories(segment, field) -> list[MemoryCreate]`

- If segment is `PERSONAL`: returns `[]` immediately.
- If segment is `MIXED`: pre-filters to sentences containing professional keywords, reducing token cost.
- Calls `EXTRACTION_PROMPT` with the segment's user messages.
- Parses the JSON response.
- Filters out memories with `confidence < settings.MIN_CONFIDENCE_THRESHOLD` (default 0.65).
- Validates each memory against the `MemoryCreate` Pydantic schema.
- On malformed JSON: logs at DEBUG level, returns `[]`.

### `process_ingestion_pipeline(segments, job_id, db) -> (int, list[MemoryCreate])`

Orchestrates extraction for a full job with rate limiting:

1. Classifies all segments in parallel
2. Filters to non-PERSONAL segments
3. Processes in batches of `EXTRACTION_BATCH_SIZE` (default 5)
4. Waits `EXTRACTION_BATCH_DELAY` seconds between batches
5. Updates `IngestionJobORM.progress` after each batch
6. Returns `(total_memories_found, all_memories)`

---

## Background Task Execution

Ingestion is always triggered as a FastAPI `BackgroundTask`, so the HTTP response returns immediately with a `job_id`.

```python
# api/ingest.py
background_tasks.add_task(_run_resume_ingestion, job_id, temp_path)
```

Background tasks create their own database session (using `async_session_factory`) because the request's `get_db()` session is closed by the time the background task runs.

```python
async def _run_resume_ingestion(job_id: str, file_path: Path) -> None:
    from database import async_session_factory
    async with async_session_factory() as db:
        # ... full pipeline ...
        await db.commit()
```

---

## Monitoring Progress

Poll `GET /api/v1/ingest/status/{job_id}`:

```json
{
  "id": "abc-123",
  "status": "processing",
  "progress": 60,
  "processed": 30,
  "total_segments": 50,
  "memories_found": 12
}
```

Status transitions: `pending` → `processing` → `complete` / `failed`

The CLI polls this endpoint every 2 seconds until `status` is `complete` or `failed`.

---

## Privacy Guarantees

- The resume parser strips all PII (email, phone, URLs) before any LLM call.
- AI export parsers send only user message text to the LLM, never the raw file.
- The extraction prompt instructs the model to replace company names with generic descriptions (`"a SaaS startup"` not `"Anthropic"`).
- Embeddings run locally — no text is sent externally for embedding.
