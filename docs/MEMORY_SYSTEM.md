# MNEMIX — Memory System

The memory system stores, retrieves, and analyzes the professional memories extracted during ingestion.

## Memory Store (`core/memory/store.py`)

Handles persistence of `MemoryCreate` objects to PostgreSQL.

### `save_memory(memory, embedding, db) -> str`

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
memory_id = await save_memory(memory, embedding, db)
```

- Generates a UUID v4 for `id`
- Serializes the embedding: `embedding.tobytes()` → BLOB
- Serializes list fields: `json.dumps(memory.themes)` → TEXT
- Returns the new memory's ID

### `get_all_memories(db) -> list[tuple[Memory, np.ndarray]]`

Returns all memories with their deserialized embeddings.

```python
memories_with_embeddings = await get_all_memories(db)
for memory, embedding in memories_with_embeddings:
    print(memory.content, embedding.shape)  # → (384,)
```

Embedding deserialization: `np.frombuffer(row.embedding, dtype=np.float32)`

### `count_memories_by_category(db) -> dict[str, int]`

Returns a dict mapping category name to count. Used by the gap detector and profile endpoint.

### `get_memory_by_id(memory_id, db) -> Memory | None`

### `increment_access_count(memory_id, db)`

Updates `access_count` and `last_accessed` on a memory. Called every time a memory is retrieved during answer evaluation. Tracks which memories are most useful for interview prep.

---

## Memory Retriever (`core/memory/retriever.py`)

In-memory semantic search using numpy vectorized cosine similarity. Much faster than SQLite queries for similarity search.

### Architecture

```python
class MemoryRetriever:
    _embeddings: np.ndarray | None  # shape (N, 384) — matrix of all memory embeddings
    _memory_ids: list[str]          # memory IDs in the same order as rows in _embeddings
    _loaded: bool
```

The matrix is loaded from the database on first `search()` call (or explicitly by calling `load()`). After that, searches are pure numpy operations — no database round-trips.

### `load(db)`

Fetches all memories from the database, stacks their embeddings into a `(N, 384)` matrix:

```python
await memory_retriever.load(db)
```

Called in `main.py` startup lifespan to warm the index before any requests. Also called lazily on the first `search()` if not yet loaded.

### `search(query_text, db, top_k=5) -> list[tuple[Memory, float]]`

Semantic search against all stored memories.

```python
results = await memory_retriever.search("technical challenge under pressure", db, top_k=5)
for memory, score in results:
    print(f"{score:.3f}  {memory.content}")
```

**Algorithm:**
1. `query_vec = embed(query_text)` — 384-dim vector
2. `similarities = _embeddings @ query_vec / (norms * query_norm + 1e-10)` — vectorized dot product over all memories in one numpy operation
3. `top_indices = np.argsort(similarities)[::-1][:top_k]`
4. Fetch the Memory objects from the database by ID
5. Return `[(Memory, similarity_score), ...]` sorted by descending similarity

Similarity scores are cosine similarities in `[-1.0, 1.0]`. In practice, relevant memories score above 0.5.

### `add_to_index(memory_id, embedding)`

Adds a new memory to the in-memory index without requiring a full reload:

```python
await memory_retriever.add_to_index(memory_id, new_embedding)
```

Called immediately after `save_memory()` during ingestion so new memories are searchable in the same session.

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

### `detect_gaps(db) -> list[dict]`

Returns a list of gap dicts for categories below minimum, sorted by priority then deficit:

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

### `get_gap_summary(db) -> str`

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
