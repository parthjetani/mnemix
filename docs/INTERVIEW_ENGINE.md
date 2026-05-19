# MNEMIX — Interview Engine

The interview engine selects questions, manages session state, evaluates answers against memories, and generates a structured feedback report.

## Question Bank (`core/interview/question_bank.py`)

### Loading Questions

`load_questions(db)` reads `data/questions_seed.json` and inserts any questions not already in the database. It's idempotent — safe to call on every startup.

The seed file path is resolved relative to the source file using:
```python
_SEED_PATH = Path(__file__).parent.parent.parent / "data" / "questions_seed.json"
```
This is Windows-safe and works regardless of the working directory.

50 questions are seeded across 18 categories. Each question has a human-readable ID (e.g., `q_leadership_001`), text starting with "Tell me about a time..." or "Describe a situation where...", and optional `field` and `seniority` constraints (NULL means universal).

### Selecting Questions

`select_questions(session_type, db, count=8)` builds a personalized set of 8 questions using a four-step algorithm:

**Step 1 — Universal opener (always first)**
One `career_goal` question. Always position 0, never shuffled. Sets context for the session.

**Step 2 — Gap questions (up to 2–3)**
Calls `detect_gaps(db)` and selects questions from the top high-priority gap categories. A user with no `leadership` memories gets a leadership question before any other behavioral question.

**Step 3 — Session-type specific fill**
Fills remaining slots from the relevant category pool:
- `behavioral`: leadership, conflict_resolution, failure_learning, collaboration, pressure_handling, initiative, communication, ambiguity_handling
- `technical`: system_design, debugging, tech_decisions, performance_optimization, architecture
- `mixed`: all behavioral + technical categories combined

Categories are shuffled before selection so different sessions use different categories.

**Step 4 — Wildcard**
One random question from any category, including identity categories (`value`, `strength`, `working_style`, `self_awareness`). Keeps sessions unpredictable.

**Final step:** Middle questions (all except the opener) are shuffled, then the list is trimmed to `count`.

---

## Session Management (`core/interview/session.py`)

### `create_session(session_type, questions, db, user_id="default") -> InterviewSession`

Creates a new interview session and persists it:
- Generates a UUID v4 session ID
- Writes `user_id` on the row so the session is visible only to its owner
- Serializes the ordered question list as JSON: `[{id, text, category}, ...]`
- Sets `status="in_progress"`

The `questions_list` column stores the full ordered question list. This makes the session self-contained — question order doesn't depend on the `questions` table state during answer submission.

### `get_next_question(session_id, db) -> dict | None`

Returns the next unanswered question:
1. Loads the session's `questions_list` JSON
2. Queries `session_answers` for already-answered question IDs
3. Returns the first question in order that hasn't been answered yet
4. Returns `None` when all questions have answers

Return format: `{"index": 0, "total": 8, "id": "q_001", "text": "...", "category": "leadership"}`

### `add_answer(session_id, question_id, question_text, answer_text, answer_order, db) -> SessionAnswer`

Inserts one answer row into `session_answers`.

### `complete_session(session_id, db)`

Sets `status="evaluating"` and records `completed_at`. Called when `get_next_question` returns `None` after the last answer.

### `get_session_answers(session_id, db) -> list[SessionAnswerORM]`

Returns all answers for a session, ordered by `answer_order`.

---

## Evaluator (`core/interview/evaluator.py`)

Scores all answers in a session using the LLM and the user's memories.

### `evaluate_session(session_id, db, user_id=None) -> list[EvaluationResult]`

1. Fetches the user profile by `user_id` to get `field` and `seniority` for the evaluation context
2. Fetches all session answers
3. Evaluates all answers **in parallel** using `asyncio.gather()`
4. Flushes score updates to the database

### `_evaluate_single_answer(answer_orm, field, seniority, db, user_id=None) -> EvaluationResult`

For each answer:

1. **Memory retrieval:** Embeds the answer text and calls `memory_retriever.search(answer_text, db, top_k=5, user_id=user_id)` — scoped to the user's own memories
2. **Task selection:** Uses `eval_sysdesign` task if the question ID contains `"sysdes"`, otherwise `eval`
3. **LLM call:** Formats `EVALUATION_PROMPT` with the question, answer, and top-5 memories as JSON context
4. **Score parsing:** Extracts `memory_match`, `specificity`, `outcome_stated`, `outcome_quantified`, `memory_opportunity_missed`, `coherence`, `specific_feedback`
5. **Normalization:** `total_score = (memory_match + specificity + (2 if outcome_stated) + (1 if outcome_quantified) + coherence) / 11 * 100`
6. **DB update:** Writes all scores back to the `session_answers` row
7. **Access tracking:** Calls `increment_access_count()` on each retrieved memory

**On LLM failure:** Returns a safe default evaluation (all zeros, generic feedback message) so the session can still complete.

### Score Dimensions

| Dimension | Range | Description |
|-----------|-------|-------------|
| `memory_match` | 0–3 | How specifically the answer references real experiences from the user's memory bank |
| `specificity` | 0–3 | Level of concrete detail: technologies, project context, numbers, timelines |
| `outcome_stated` | bool | Whether the answer described the result of the user's actions |
| `outcome_quantified` | bool | Whether the outcome included measurable numbers |
| `coherence` | 0–2 | Answer structure and clarity (situation → action → result) |

Max raw score: 3 + 3 + 2 + 1 + 2 = 11 → normalized to 100.

---

## Feedback Generator (`core/interview/feedback.py`)

### `generate_feedback(session_id, evaluations, db, user_id=None) -> FeedbackReport`

1. Calculates `overall_score = mean([e.total_score for e in evaluations])`
2. Fetches the user profile by `user_id` for context
3. Serializes all evaluations (truncating answer text to 300 chars) into JSON
4. Calls `FEEDBACK_PROMPT` with overall score, profile summary, and all evaluations
5. Updates the session: sets `status="complete"`, `overall_score`, `feedback_report` (full text)
6. Returns `FeedbackReport`

**On LLM failure:** `_fallback_report()` generates a plain-text report from the scores alone, without LLM narrative.

### Report Format

The LLM generates a structured text report following a fixed template:

```
═══════════════════════════════════════════════
MNEMIX INTERVIEW REPORT
═══════════════════════════════════════════════

OVERALL SCORE: 72/100
VERDICT: [One honest sentence]

───────────────────────────────────────────────
PER-QUESTION BREAKDOWN
───────────────────────────────────────────────

Q1: [Question summary]
What worked: [specific strength]
What was missing: [specific gap]
Suggestion: [exact improvement]

...

───────────────────────────────────────────────
PATTERNS ACROSS ALL ANSWERS
───────────────────────────────────────────────

Consistent strengths: ...
Consistent weaknesses: ...
Most important fix: ...

───────────────────────────────────────────────
NEXT SESSION PLAN
───────────────────────────────────────────────

Practice: ...
Stories to build: ...
Focus questions: ...

═══════════════════════════════════════════════
```

---

## Full Session Lifecycle

```
POST /interview/start
  └── select_questions()           — opener + gaps + type-specific + wildcard
  └── create_session(..., user_id) — status=in_progress, questions_list + user_id saved
  └── get_next_question()          — returns first question
  └── Response: {session_id, total_questions, current_question}

[for each question]
POST /interview/answer
  └── add_answer()                 — row saved in session_answers
  └── get_next_question()
      ├── if more → return next question
      └── if last → complete_session() (status=evaluating)
                 → BackgroundTask: _run_evaluation(session_id)
                     └── evaluate_session()   — parallel LLM calls
                     └── generate_feedback()  — final report
                     └── db.commit()

GET /interview/evaluate/{session_id}
  ├── status=evaluating → {"status": "evaluating"}  (poll again)
  └── status=complete   → FeedbackReport with per-question scores
```

Background evaluation typically takes 30–90 seconds depending on the number of questions and LLM response times. The CLI polls every 5 seconds with a 10-minute timeout.
