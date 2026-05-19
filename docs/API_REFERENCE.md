# MNEMIX — API Reference

All endpoints are prefixed with `/api/v1`. The server runs on `http://localhost:8000` by default (uvicorn default port).

## Authentication

All endpoints except `GET /api/v1/health` require a Supabase JWT in the `Authorization` header:

```
Authorization: Bearer <supabase-access-token>
```

Without a valid token the server returns `401`. During local development with `DEBUG=true`, the token `dev-local` is accepted as a bypass:

```
Authorization: Bearer dev-local
```

---

## Health

### `GET /api/v1/health`

Returns server status.

**Response:**
```json
{"status": "ok", "version": "0.1.0"}
```

---

## Ingestion

### `POST /api/v1/ingest/resume`

Upload a resume PDF for memory extraction.

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | PDF file. Content-Type: `application/pdf` |

**Response `200`:**
```json
{
  "job_id": "a3f9b2c1-...",
  "status": "pending",
  "message": "Resume ingestion started"
}
```

**Response `400`:** Non-PDF file uploaded.

Extraction runs as a background job. Poll `GET /ingest/status/{job_id}` for progress.

---

### `POST /api/v1/ingest/ai-export`

Upload a ChatGPT or Claude conversation export.

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | ZIP, JSON, or MD file |
| `source_type` | string | `chatgpt` or `claude` |

**Response `200`:**
```json
{
  "job_id": "b7d3e4f5-...",
  "status": "pending",
  "message": "ChatGPT export ingestion started"
}
```

**Response `400`:** Unknown `source_type`.

---

### `GET /api/v1/ingest/status/{job_id}`

Poll ingestion job status.

**Response `200`:**
```json
{
  "id": "a3f9b2c1-...",
  "source_type": "resume",
  "status": "complete",
  "total_segments": 12,
  "processed": 12,
  "progress": 100,
  "memories_found": 8,
  "started_at": "2026-05-18T10:00:00+00:00",
  "completed_at": "2026-05-18T10:01:30+00:00",
  "error_message": null
}
```

`status` values: `pending` → `processing` → `complete` / `failed`

**Response `404`:** Job not found.

---

## Memory

### `GET /api/v1/memory/profile`

Returns memory counts by category and user profile.

**Response `200`:**
```json
{
  "total_memories": 45,
  "by_category": {
    "technical_achievement": 12,
    "leadership": 8,
    "failure_learning": 5,
    "system_design": 3
  },
  "top_memories": [
    {
      "id": "c1d2e3f4-...",
      "content": "Led a Django to FastAPI migration reducing latency by 40%",
      "category": "technical_achievement",
      "access_count": 7,
      "last_accessed": "2026-05-18T11:00:00+00:00"
    }
  ],
  "profile": {
    "field": "software_engineering",
    "seniority": "mid",
    "career_narrative": null
  }
}
```

Top memories are sorted by `access_count` descending, limited to 10.

---

### `GET /api/v1/memory/gaps`

Returns memory categories below minimum coverage.

**Response `200`:**
```json
{
  "gaps": [
    {
      "category": "leadership",
      "have": 1,
      "need": 3,
      "priority": "high",
      "deficit": 2,
      "suggested_questions": [
        "Tell me about a time you led a team through a difficult technical decision..."
      ]
    },
    {
      "category": "conflict_resolution",
      "have": 0,
      "need": 2,
      "priority": "high",
      "deficit": 2,
      "suggested_questions": []
    }
  ]
}
```

High-priority gaps include LLM-generated `suggested_questions`. Medium/low gaps return an empty list.

---

### `POST /api/v1/memory/add`

Manually add a memory.

**Request body:**
```json
{
  "content": "Designed and implemented a microservices migration...",
  "category": "architecture",
  "themes": ["distributed systems", "migration"]
}
```

**Response `200`:**
```json
{
  "id": "d4e5f6a7-...",
  "content": "Designed and implemented a microservices migration...",
  "category": "architecture",
  "source": "manual",
  "created_at": "2026-05-18T12:00:00+00:00"
}
```

**Response `400`:** Invalid `category` value.

---

### `GET /api/v1/memory/search?q={query}&top_k={n}`

Semantic search over stored memories.

**Query parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `q` | yes | — | Search query text |
| `top_k` | no | 5 | Number of results to return |

**Response `200`:** Array of results, sorted by descending similarity.
```json
[
  {
    "memory": {
      "id": "...",
      "content": "...",
      "category": "technical_achievement",
      "themes": ["backend", "performance"],
      "confidence": 0.9,
      "has_outcome": true,
      "outcome_quantified": false,
      "source": "chatgpt",
      "created_at": "2026-05-18T10:00:00+00:00",
      "access_count": 3
    },
    "similarity": 0.823
  }
]
```

---

## Interview

### `POST /api/v1/interview/start`

Start a new mock interview session.

**Request body:**
```json
{
  "session_type": "behavioral",
  "num_questions": 8
}
```

`session_type`: `behavioral`, `technical`, or `mixed`. `num_questions` is accepted but the server uses `INTERVIEW_QUESTIONS_COUNT` from config (default 8).

**Response `200`:**
```json
{
  "session_id": "e5f6a7b8-...",
  "session_type": "behavioral",
  "total_questions": 8,
  "current_question": {
    "index": 0,
    "total": 8,
    "id": "q_career_001",
    "text": "Tell me about yourself and your current role.",
    "category": "career_goal"
  }
}
```

**Response `500`:** No questions in the database. Restart the server to trigger the seed.

---

### `POST /api/v1/interview/answer`

Submit an answer to the current question.

**Request body:**
```json
{
  "session_id": "e5f6a7b8-...",
  "question_id": "q_leadership_003",
  "question_text": "Tell me about a time you led a team...",
  "answer_text": "In my previous role at a SaaS startup...",
  "answer_order": 2
}
```

All fields are required. `answer_order` is 0-indexed.

**Response `200` (more questions):**
```json
{
  "session_complete": false,
  "session_id": "e5f6a7b8-...",
  "next_question": {
    "index": 3,
    "total": 8,
    "id": "q_conflict_001",
    "text": "Describe a situation where you disagreed with...",
    "category": "conflict_resolution"
  }
}
```

**Response `200` (last answer):**
```json
{
  "session_complete": true,
  "session_id": "e5f6a7b8-...",
  "next_question": null,
  "message": "All answers received. Evaluation in progress."
}
```

When `session_complete` is true, a background evaluation task has been triggered.

**Response `404`:** Session not found.
**Response `400`:** Session is not in `in_progress` or `evaluating` status.

---

### `GET /api/v1/interview/evaluate/{session_id}`

Get evaluation results. Poll until status is not `evaluating`.

**Response `200` (still evaluating):**
```json
{
  "status": "evaluating",
  "message": "Evaluation in progress, try again in a few seconds"
}
```

**Response `200` (complete):**
```json
{
  "session_id": "e5f6a7b8-...",
  "overall_score": 72.3,
  "report_text": "═══════ MNEMIX INTERVIEW REPORT ═══════\n...",
  "evaluations": [
    {
      "question_id": "q_career_001",
      "question_text": "Tell me about yourself...",
      "answer_text": "I'm a full-stack developer...",
      "memory_match": 2,
      "specificity": 3,
      "outcome_stated": true,
      "outcome_quantified": false,
      "memory_opportunity_missed": null,
      "coherence": 2,
      "specific_feedback": "Add quantified outcomes — e.g. 'reduced deploy time by 60%'",
      "total_score": 81.8
    }
  ]
}
```

**Response `404`:** Session not found.

---

### `GET /api/v1/interview/sessions`

List past interview sessions, most recent first (limit 20).

**Response `200`:**
```json
[
  {
    "id": "e5f6a7b8-...",
    "session_type": "behavioral",
    "status": "complete",
    "started_at": "2026-05-18T10:00:00+00:00",
    "completed_at": "2026-05-18T10:25:00+00:00",
    "overall_score": 72.3
  }
]
```

---

## Error Format

All errors return a `detail` field:

```json
{"detail": "Session not found"}
```

or with a structured detail:

```json
{"detail": {"error": "Unsupported file type", "code": "INVALID_FILE"}}
```

HTTP status codes: 400 (bad input), 404 (not found), 422 (schema validation), 500 (LLM or server error).
