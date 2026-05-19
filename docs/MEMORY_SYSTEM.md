# MNEMIX — Memory System

The memory system stores, retrieves, and analyzes the professional memories extracted during ingestion.

## Memory Store (`core/memory/store.py`)

Handles persistence of `MemoryCreate` objects to PostgreSQL.

### `save_memory(memory, embedding, db, user_id="default") -> str`

Saves a single memory to the database.

```python
from core.memory.store import save_memory
from llm.embeddings import embed
from models.schemas import MemoryCreate

memory = MemoryCreate(
    content="Led a Django to FastAPI migration, reducing API latency by 40%",
    category="technical_achievement",
    themes=["backend", "performance"],
    interview_qs=["Tell me about a technical challenge..."],
    confidence=0.9,
    source="chatgpt",
    has_outcome=True,
    outcome_quantified=True,
)
embedding = embed(memory.content)
memory_id = await save_memory(memory, embedding, db, user_id=ctx.user_id)
```

- Generates a UUID v4 for `id`
- Writes `user_id` on the row for per-user isolation
- Dual-writes the embedding: `embedding.tobytes()` → `embedding` (BLOB, legacy) and `embedding.tolist()` → `embedding_vec` (vector(384), pgvector)
- Serializes list fields: `json.dumps(memory.themes)` → TEXT
- Returns the new memory's ID

### `get_all_memories(db, user_id=None) -> list[tuple[Memory, np.ndarray]]`

Returns memories with their deserialized embeddings. Filters by `user_id` when provided.

### `count_memories_by_category(db, user_id=None) -> dict[str, int]`

Returns a dict mapping category name to count, filtered by `user_id`. Used by the gap detector and profile endpoint.

### `get_memory_by_id(memory_id, db) -> Memory | None`

### `increment_access_count(memory_id, db)`

Updates `access_count` and `last_accessed` on a memory. Called every time a memory is retrieved during answer evaluation. Tracks which memories are most useful for interview prep.

---

## Memory Retriever (`core/memory/retriever_pgvector.py`)

pgvector-backed semantic search using PostgreSQL's `<=>` cosine distance operator and an HNSW index. Process-stateless — multiple uvicorn workers behave correctly.

### `search(query_text, db, top_k=5, user_id=None) -> list[tuple[Memory, float]]`

Semantic search scoped to the given user.

```python
results = await memory_retriever.search(
    "technical challenge under pressure", db, top_k=5, user_id=ctx.user_id
)
for memory, score in results:
    print(f"{score:.3f}  {memory.content}")
```

**Algorithm:**
1. `query_vec = embed(query_text)` — 384-dim float32 vector
2. SQL: `ORDER BY embedding_vec <=> :query_vec ASC WHERE user_id = :uid LIMIT :k` — HNSW index returns the k nearest rows by cosine distance
3. `similarity = 1 - cosine_distance` — converted so higher is better
4. IDs + similarities fetched; `get_memories_by_ids()` materialises the full Memory objects in one batch query
5. Returns `[(Memory, similarity), ...]` in descending similarity order

### `add_to_index(memory_id, embedding)` — no-op

pgvector search reads directly from the `embedding_vec` column written by `save_memory()`. There is no in-memory index to update. The call site signature is preserved so call sites don't need changes.

### `load(db)` — no-op

No warm-up index to populate. Removed from `main.py` startup lifespan.

---

## Gap Detector (`core/memory/gap_detector.py`)

Analyzes which interview categories have insufficient memory coverage.

### Required Coverage

`REQUIRED_CATEGORIES` defines the minimum story count and priority for 13 key categories:

| Category | Minimum | Priority |
|----------|---------|----------|
| `leadership` | 3 | high |
| `conflict_resolution` | 2 | high |
| `failure_learning` | 2 | high |
| `technical_achievement` | 3 | high |
| `system_design` | 1 | high |
| `tech_decisions` | 2 | high |
| `collaboration` | 2 | medium |
| `ambiguity_handling` | 2 | medium |
| `initiative` | 2 | medium |
| `debugging` | 2 | medium |
| `career_goal` | 1 | medium |
| `strength` | 2 | medium |
| `value` | 1 | low |

### `detect_gaps(db, user_id=None) -> list[dict]`

Returns a list of gap dicts for categories below minimum, scoped to the given user, sorted by priority then deficit:

```json
[
  {
    "category": "leadership",
    "have": 1,
    "need": 3,
    "priority": "high",
    "deficit": 2,
    "suggested_questions": ["Tell me about a time you led a team through a difficult project..."]
  }
]
```

For `high` priority gaps, `detect_gaps()` calls `GAP_ANALYSIS_PROMPT` to generate suggested fill questions. Medium and low priority gaps return without suggested questions (saves LLM calls).

### `get_gap_summary(db, user_id=None) -> str`

Returns a formatted text summary suitable for terminal display. Used internally — the CLI uses the raw gap list from `detect_gaps()` to build its own Rich table.

---

## Memory in the Interview Flow

During answer evaluation, the evaluator:

1. Embeds the user's answer: `embed(answer_text)`
2. Calls `memory_retriever.search(answer_text, db, top_k=5)`
3. Passes the top-5 memories to `EVALUATION_PROMPT` as context
4. The LLM scores `memory_match` (0–3): how well the answer uses those real experiences
5. Calls `increment_access_count()` on each retrieved memory

This creates a feedback loop: memories that are actually relevant to interview answers get higher access counts, which can be used to surface the most interview-relevant experiences.

---

## Memory Profile

`GET /api/v1/memory/profile` returns:

```json
{
  "total_memories": 45,
  "by_category": {
    "technical_achievement": 12,
    "leadership": 8,
    "failure_learning": 5,
    ...
  },
  "top_memories": [
    {
      "id": "...",
      "content": "Led a Django to FastAPI migration...",
      "category": "technical_achievement",
      "access_count": 7
    }
  ],
  "profile": {
    "field": "software_engineering",
    "seniority": "mid"
  }
}
```
