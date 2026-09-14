# MNEMIX — LLM System

All LLM interactions go through `llm/router.py`. Core modules never import or instantiate LLM clients directly. All prompt templates live in `llm/prompts.py`.

## Router (`llm/router.py`)

### Providers

Three OpenAI-compatible client instances are initialized at module load:

```python
groq_client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)
nvidia_client = AsyncOpenAI(api_key=settings.NVIDIA_API_KEY or "unset", base_url=settings.NVIDIA_BASE_URL)
gemini_client = AsyncOpenAI(api_key=settings.GEMINI_API_KEY or "unset", base_url=settings.GEMINI_BASE_URL)
```

There is no single "primary" provider anymore — each task has its own ordered chain (see below). A provider slot with no API key configured is marked `enabled=False` and skipped without making a network call.

### Task Routing

Every LLM call specifies a task string. `TASK_CHAINS` maps each task to an ordered list of `ProviderSlot`s, tried in order:

| Task | Chain (in order) | Use |
|------|-------------------|-----|
| `classify` | Groq 8B → Gemini Gemma4 → NIM Llama-8B | Classify ambiguous conversation segments |
| `extract` | NIM DeepSeek-v4-flash → Gemini Flash-Lite → Groq 70B | Extract memories from professional content |
| `profile` | NIM DeepSeek-v4-pro → Gemini Flash-Lite → Groq 70B | Synthesize user profile from memory summary |
| `q_behavioral` | Groq gpt-oss-20b → NIM Llama-8B | Generate a behavioral interview question |
| `q_technical` | Groq qwen3-32b → NIM Qwen3-coder-480b | Generate a technical interview question |
| `eval` | NIM Kimi-k2-thinking → Groq 70B | Evaluate behavioral/technical answers |
| `eval_sysdesign` | NIM Kimi-k2-thinking → Groq qwen3-32b | Evaluate system design answers (reasoning model) |
| `feedback` | NIM Kimi-k2-thinking → Gemini Flash-Lite → Groq 70B | Generate final feedback report |
| `gap_analysis` | Groq qwen3-32b → NIM Llama-8B | Generate questions for memory gap categories |

Model names and chain composition are defined in `llm/router.py` (`TASK_CHAINS`); the individual model IDs come from `config.py` settings — change them via `.env`.

`profile` synthesis is triggered by `POST /api/v1/profile/synthesize` (`core/memory/profile_synthesizer.py`), called automatically when ingestion completes and manually via a "Regenerate Profile" button. `q_behavioral`/`q_technical` are called from `core/interview/question_bank.py::select_questions()` — the session-type-specific portion of question selection is generated per-user in parallel via `asyncio.gather` (`core/interview/question_generator.py`), with the static seeded question bank as a per-category fallback if generation fails. The opener, gap-filling, and wildcard questions always stay seeded.

### Calling the Router

```python
from llm.router import llm_router, LLMError

result = await llm_router.call(
    task="extract",
    prompt="...",
    system="Optional system message",  # prepended to messages if provided
    max_tokens=1000,
)
```

Returns the raw string content from the LLM response.

### Fallback Strategy

`LLMRouter.call()` walks the task's chain in order:

1. Skip any provider slot that's `disabled` (no API key configured) or whose `QuotaTracker` reports exhausted (RPD cap hit, or a prior `RateLimitError` marked it exhausted for the rest of the day)
2. On `RateLimitError`, mark that provider exhausted until the next day-rollover, respect `Retry-After` (capped at 5s), and fall through to the next provider
3. On any other `OpenAIError`, log and fall through to the next provider
4. Raise `LLMError` only once every provider in the chain has been skipped, rate-limited, or failed

`QuotaTracker` state (RPM sliding window + RPD counter) is in-process only — correct for a single worker/process, not multi-worker/multi-pod (fine for the current local-only deployment; would need a Redis-backed counter to scale out).

All callers in `core/` catch `LLMError` and either return a safe default or raise `HTTPException(500)`.

### JSON Parsing

```python
parsed = llm_router.parse_json_response(text)
```

`parse_json_response` handles:
1. Strips `<think>...</think>` blocks (emitted by qwen3 and deepseek-r1 before the answer)
2. Strips markdown code fences (` ```json ... ``` `)
3. Finds the first `{` or `[` in the remaining text and extracts from there
4. Calls `json.loads()` on the extracted string

Raises `ValueError` if no valid JSON is found.

For prompts that return plain text instead of JSON (like `Q_TECHNICAL_PROMPT`, which runs on the reasoning model `qwen3-32b`), use `llm_router.strip_plain_text(text)` — strips the same `<think>...</think>` block without attempting JSON extraction.

---

## Prompts (`llm/prompts.py`)

Eight module-level string constants. No logic — format strings only.

### `CLASSIFICATION_PROMPT`

**Task:** Classify a conversation segment as PROFESSIONAL, BEHAVIORAL_PRO, MIXED, or PERSONAL.

**Input variables:** `{user_messages}`

**Output:** `{"category": "...", "confidence": 0.0}`

**Max tokens:** 50

Used by `core/processing/classifier.py` only for segments that don't match the keyword rules. Most segments are classified without any LLM call.

---

### `EXTRACTION_PROMPT`

**Task:** Extract structured professional memories from a conversation segment.

**Input variables:** `{field}`, `{role}`, `{user_messages}`

**Output:**
```json
{
  "memories": [
    {
      "content": "One-sentence memory description",
      "category": "technical_achievement",
      "themes": ["backend", "performance"],
      "interview_qs": ["Tell me about a technical challenge..."],
      "confidence": 0.85,
      "has_outcome": true,
      "outcome_quantified": true,
      "date_context": "2024"
    }
  ]
}
```

**Max tokens:** 1000

**Critical rules baked into the prompt:**
- Extract only from USER messages, never AI responses
- Content must use generic descriptions (no real company names)
- Minimum confidence 0.65 to include
- Return `{"memories": []}` if nothing qualifies
- Never extract personal life content

---

### `PROFILE_PROMPT`

**Task:** Synthesize a user profile from memory statistics and sample memories.

**Input variables:** `{field}`, `{memory_summary}`, `{sample_memories}`

**Output:** JSON with `communication_style`, `strength_areas`, `gap_areas`, `career_narrative`.

Used by `core/memory/profile_synthesizer.py::synthesize_profile()`. On LLM failure, falls back to a heuristic derived straight from category counts (`strength_areas` = categories with 3+ memories, `gap_areas` = categories with 0-1) rather than leaving the profile empty.

---

### `Q_BEHAVIORAL_PROMPT`

**Task:** Generate one behavioral interview question for a specific category.

**Input variables:** `{category}`, `{profile_summary}`

**Output:** Plain text question (no JSON).

Questions must start with "Tell me about a time..." or "Describe a situation where..." — forces specificity.

---

### `Q_TECHNICAL_PROMPT`

**Task:** Generate one technical interview question.

**Input variables:** `{category}`, `{stack}`, `{seniority}`

**Output:** Plain text question. `qwen3-32b` is a reasoning model — the response is passed through `llm_router.strip_plain_text()` before use, and `max_tokens` is set generously (~900) since the hidden `<think>` block consumes most of the budget.

---

### `EVALUATION_PROMPT`

**Task:** Score one interview answer across five dimensions.

**Input variables:** `{field}`, `{seniority}`, `{question}`, `{answer}`, `{top_memories}`, `{memory_summary}`

**Output:**
```json
{
  "memory_match": 2,
  "specificity": 3,
  "outcome_stated": true,
  "outcome_quantified": false,
  "memory_opportunity_missed": null,
  "coherence": 2,
  "specific_feedback": "Add the 40% latency reduction number from your FastAPI migration."
}
```

**Score dimensions:**
- `memory_match` (0–3): How well the answer references real experiences from `top_memories`
- `specificity` (0–3): Level of concrete detail (technologies, project context, timelines)
- `outcome_stated` (bool): Did the answer describe what resulted from their actions?
- `outcome_quantified` (bool): Did the outcome include numbers or metrics?
- `memory_opportunity_missed` (string|null): ID of a memory that would have answered this better
- `coherence` (0–2): Clarity and structure of the answer

**Normalized total score:** `(memory_match + specificity + (2 if outcome_stated) + (1 if outcome_quantified) + coherence) / 11 * 100`

---

### `FEEDBACK_PROMPT`

**Task:** Generate the full post-session feedback report.

**Input variables:** `{field}`, `{profile_summary}`, `{all_evaluations}`, `{score}`

**Output:** Formatted text (not JSON) following a fixed template with sections: OVERALL SCORE, PER-QUESTION BREAKDOWN, PATTERNS ACROSS ALL ANSWERS, NEXT SESSION PLAN.

**Max tokens:** 1500

---

### `GAP_ANALYSIS_PROMPT`

**Task:** Generate suggested questions to help users fill memory gaps.

**Input variables:** `{gap_categories}`, `{memory_counts}`

**Output:** `{"gap_questions": [{"category": "...", "question": "..."}]}`

---

## Embeddings (`llm/embeddings.py`)

Local sentence-transformers wrapper. No API calls.

**Model:** `all-MiniLM-L6-v2` (384-dimensional output, ~90MB download)

**Lazy loading:** The model is not loaded until the first `embed()` call. `main.py` calls `embed("warmup")` during startup to trigger the download before any requests arrive.

```python
from llm.embeddings import embed, cosine_similarity

# Single embedding — cached by text content
vector = embed("Led a Django to FastAPI migration, reduced latency by 40%")
# → np.ndarray of shape (384,), dtype float32

# Similarity
score = cosine_similarity(vec_a, vec_b)
# → float in [-1.0, 1.0]
```

**Cache:** `_cache: dict[str, np.ndarray]` is a module-level dict. The same text is never encoded twice in a single server process. Cache is not persisted across restarts.

## Rate Limiting

The Groq free tier allows 6,000 tokens/minute. The ingestion pipeline respects this with:
- `EXTRACTION_BATCH_SIZE=5` segments per LLM call
- `EXTRACTION_BATCH_DELAY=2.0s` between batches

These are configured via `.env` and loaded into `settings.EXTRACTION_BATCH_SIZE` / `settings.EXTRACTION_BATCH_DELAY`.
