# MNEMIX — Database Schema

MNEMIX uses SQLite via SQLAlchemy 2.0 async ORM. The database file is `mnemix.db` in the working directory.

All tables are created on server startup via `init_db()` in `database.py` using `Base.metadata.create_all`.

## ORM Class Names vs Table Names

| ORM Class | Table Name | Purpose |
|-----------|------------|---------|
| `MemoryORM` | `memories` | Extracted professional memories with embeddings |
| `InterviewSessionORM` | `interview_sessions` | One record per mock interview run |
| `SessionAnswerORM` | `session_answers` | One record per question-answer pair |
| `QuestionORM` | `questions` | Seeded and learned interview questions |
| `IngestionJobORM` | `ingestion_jobs` | Async ingestion job tracking |
| `UserProfileORM` | `user_profile` | Single-row user profile |

---

## `memories`

Stores extracted professional memories and their embeddings.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT PK | — | UUID v4 string |
| `content` | TEXT NOT NULL | — | One-sentence memory description (anonymized) |
| `category` | TEXT NOT NULL | — | One of 19 memory categories (see below) |
| `themes` | TEXT | — | JSON array of tag strings, e.g. `["backend", "performance"]` |
| `interview_qs` | TEXT | — | JSON array of interview questions this memory answers |
| `confidence` | REAL | 0.0 | Extraction confidence score (0.0–1.0) |
| `source` | TEXT | — | `resume`, `chatgpt`, `claude`, or `manual` |
| `date_context` | TEXT | NULL | Approximate date if mentioned in source |
| `has_outcome` | INTEGER | 0 | Boolean (1/0): memory includes a described outcome |
| `outcome_quantified` | INTEGER | 0 | Boolean (1/0): outcome includes numbers or metrics |
| `embedding` | BLOB | NULL | numpy float32 array serialized via `.tobytes()` (384 floats = 1,536 bytes) |
| `created_at` | TEXT | `datetime('now')` | ISO 8601 timestamp |
| `access_count` | INTEGER | 0 | Times this memory was retrieved during answer evaluation |
| `last_accessed` | TEXT | NULL | ISO 8601 timestamp of last retrieval |

**Array columns** (`themes`, `interview_qs`) are stored as JSON strings because SQLite has no native array type. Deserialize with `json.loads()`.

**Embedding** is stored as a raw BLOB. Deserialize with:
```python
np.frombuffer(row.embedding, dtype=np.float32)
```

---

## `interview_sessions`

One row per mock interview session.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT PK | — | UUID v4 string |
| `started_at` | TEXT | `datetime('now')` | ISO 8601 timestamp |
| `completed_at` | TEXT | NULL | Set when last answer is submitted |
| `session_type` | TEXT | — | `behavioral`, `technical`, or `mixed` |
| `overall_score` | REAL | NULL | Mean score across all answers (0–100). Set after evaluation. |
| `status` | TEXT | `in_progress` | `in_progress` → `evaluating` → `complete` |
| `questions_list` | TEXT | NULL | JSON array of `{id, text, category}` objects — the ordered question list for this session |
| `feedback_report` | TEXT | NULL | Full text of the LLM-generated feedback report |

**Status lifecycle:**
```
in_progress  →  (last answer submitted)  →  evaluating  →  (LLM eval done)  →  complete
```

---

## `session_answers`

One row per question-answer pair within a session.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT PK | — | UUID v4 string |
| `session_id` | TEXT | — | FK → `interview_sessions.id` |
| `question_id` | TEXT | — | FK → `questions.id` |
| `question_text` | TEXT | — | Question text (denormalized for stability) |
| `answer_text` | TEXT | NULL | User's full answer |
| `answer_order` | INTEGER | — | 0-indexed position in the session |
| `memory_match_score` | REAL | NULL | LLM score 0–3: how well the answer references real memories |
| `specificity_score` | REAL | NULL | LLM score 0–3: level of concrete detail |
| `outcome_stated` | INTEGER | 0 | Boolean: did the answer describe a result? |
| `outcome_quantified` | INTEGER | 0 | Boolean: did the result include numbers? |
| `memory_opportunity` | TEXT | NULL | Memory ID of a better story the user could have told |
| `coherence_score` | REAL | NULL | LLM score 0–2: structure and clarity |
| `total_score` | REAL | NULL | Normalized 0–100 score |
| `feedback_text` | TEXT | NULL | One-sentence actionable feedback for this answer |
| `created_at` | TEXT | — | ISO 8601 timestamp |

**Score normalization formula:**
```
total_score = (memory_match + specificity + (2 if outcome_stated else 0)
               + (1 if outcome_quantified else 0) + coherence) / 11 * 100
```
Maximum raw score: 3 + 3 + 2 + 1 + 2 = 11.

---

## `questions`

Pre-seeded and learned interview questions.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT PK | — | Human-readable slug, e.g. `q_leadership_001` |
| `text` | TEXT NOT NULL | — | Full question text |
| `category` | TEXT | — | One of 19 memory categories |
| `field` | TEXT | NULL | `software_engineering`, `product`, etc. NULL = universal |
| `seniority` | TEXT | NULL | `junior`, `mid`, `senior`. NULL = all levels |
| `source` | TEXT | `seeded` | `seeded` or `learned` |
| `effectiveness_score` | REAL | 0.5 | 0.0–1.0. Updated as sessions provide signal. |
| `use_count` | INTEGER | 0 | Times selected in a session |
| `created_at` | TEXT | `datetime('now')` | ISO 8601 timestamp |

The seed file is `data/questions_seed.json`. Questions are inserted on server startup (idempotent — skips already-existing IDs).

---

## `ingestion_jobs`

Tracks async ingestion operations initiated via the API.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | TEXT PK | — | UUID v4 string |
| `source_type` | TEXT | — | `resume`, `chatgpt`, or `claude` |
| `status` | TEXT | `pending` | `pending` → `processing` → `complete` / `failed` |
| `total_segments` | INTEGER | 0 | Total segments found in the source |
| `processed` | INTEGER | 0 | Segments processed so far |
| `progress` | INTEGER | 0 | Percentage complete (0–100) |
| `memories_found` | INTEGER | 0 | Memories extracted and saved |
| `started_at` | TEXT | NULL | ISO 8601 timestamp when processing began |
| `completed_at` | TEXT | NULL | ISO 8601 timestamp when finished |
| `error_message` | TEXT | NULL | Error detail if status is `failed` |
| `created_at` | TEXT | — | ISO 8601 timestamp when job was created |

---

## `user_profile`

Single-row table (id=1 always). Stores synthesized user profile.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | INTEGER PK | 1 | Always 1 — enforces single-user constraint |
| `field` | TEXT | `software_engineering` | Professional domain |
| `seniority` | TEXT | `mid` | Career level: `junior`, `mid`, `senior` |
| `primary_stack` | TEXT | NULL | JSON array of technology strings |
| `target_roles` | TEXT | NULL | JSON array of role strings |
| `communication_style` | TEXT | NULL | JSON object describing communication patterns |
| `strength_areas` | TEXT | NULL | JSON array of strong memory categories |
| `gap_areas` | TEXT | NULL | JSON array of weak memory categories |
| `career_narrative` | TEXT | NULL | 2-sentence professional summary |
| `last_updated` | TEXT | `datetime('now')` | ISO 8601 timestamp |

---

## Memory Categories

The 19 valid values for `memories.category` and `questions.category`:

**Behavioral:**
`leadership`, `conflict_resolution`, `failure_learning`, `technical_achievement`, `collaboration`, `ambiguity_handling`, `initiative`, `communication`, `pressure_handling`

**Technical:**
`system_design`, `debugging`, `tech_decisions`, `performance_optimization`, `architecture`

**Identity:**
`career_goal`, `value`, `strength`, `working_style`, `self_awareness`

---

## Async Access Pattern

All database access uses async SQLAlchemy with aiosqlite:

```python
# In FastAPI endpoints — use the get_db() dependency
async def endpoint(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MemoryORM))
    memories = result.scalars().all()

# In background tasks — create own session
from database import async_session_factory
async with async_session_factory() as db:
    ...
    await db.commit()
```

`get_db()` commits on success and rolls back on exception. Background tasks must commit explicitly.
