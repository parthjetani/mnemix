# MNEMIX
## Complete Founder-Level Product Documentation
### Version 1.0 — Demo Build

---

> **One Line:** MNEMIX is an AI interview intelligence system that builds a deep personal memory from your documents and AI history, then conducts realistic interviews using your actual experiences — getting smarter with every user it serves.

---

## Table of Contents

1. Product Vision
2. The Problem We Solve
3. How MNEMIX Works — User Journey
4. System Architecture
5. The Two Core Engines
6. The Self-Improvement Engine
7. Latency Strategy
8. Data Schema
9. API Design
10. Build Plan (Demo v0.1)
11. Technology Stack
12. Cost Model
13. Future Roadmap
14. Investor Narrative

---

## 1. Product Vision

### What MNEMIX Is

MNEMIX is a memory-powered AI interview system built for software engineers, product engineers, and data engineers.

Unlike every other interview tool on the market — ParakeetAI, LockedIn AI, Final Round AI, Cluely — MNEMIX does not generate generic answers from a resume. It mines two years of your actual AI conversation history, your real project work, your genuine communication patterns, and builds a deep personal memory profile that makes every interview answer sound provably, verifiably like you.

MNEMIX then conducts realistic mock interviews using that memory, evaluates your answers silently, and delivers structured feedback after each session. In the background, MNEMIX learns from every interview session across all users — improving question quality, answer evaluation, and personalization for everyone on the platform.

### The North Star

**Minimum latency. Maximum personalization. Both at the same time.**

Every architectural decision, every model choice, every engineering tradeoff in MNEMIX points at these two goals simultaneously. They are not in tension — they are the same goal approached from different angles.

---

## 2. The Problem We Solve

### The Generic Answer Problem

Every AI interview tool today follows the same pipeline:

```
Resume + Job Description → LLM → Generic Answer
```

The result sounds like this:

> "In my previous role, I led a team of engineers to deliver a critical project on time. I used strong communication skills and prioritized effectively."

No interviewer is impressed by this. No hiring manager believes it. Experienced interviewers identify AI-generated answers within two follow-up questions because the answers have no specific detail, no authentic voice, no verifiable grounding.

### What MNEMIX Does Instead

```
2 Years of YOUR AI History
+ Your Real Projects
+ Your Communication Patterns
+ Your Actual Stories
→ Answer that is provably YOU
```

The result sounds like this:

> "Eight months ago I was working on Veda — a WhatsApp health coaching bot on FastAPI and Supabase. We had a race condition in our upsert logic that was silently corrupting user health data across thousands of records. I caught it during a routine audit. The fix required coordinating a zero-downtime migration while keeping the client calm. What I learned was that SELECT-then-INSERT patterns are fundamentally unsafe in concurrent systems — you need atomic upsert or you need locks."

That answer survives ten follow-up questions. It references real technology, real consequences, real learning. An interviewer cannot distinguish it from a genuine human response because it IS a genuine human response — sourced from the user's real experience.

### The Market Gap

After reviewing 15+ competitors in this space:

| Competitor | Personalization Method | Personal Memory | Answer Authenticity |
|---|---|---|---|
| ParakeetAI | Resume keywords | ❌ | Generic |
| LockedIn AI | Resume + JD | ❌ | Generic |
| Final Round AI | Resume + JD | ❌ | Generic |
| Cluely | Screen + audio | ❌ | Generic |
| Chiku AI | Resume | ❌ | Generic |
| **MNEMIX** | **Full AI history + stories** | **✅** | **Authentic** |

The gap is absolute. Nobody has personal memory. Nobody is building it. This is MNEMIX's entire moat.

---

## 3. How MNEMIX Works — User Journey

### Phase 1: Memory Ingestion

```
User provides:
├── Resume (PDF)
└── AI export history (ZIP)
    ├── ChatGPT: conversations.json
    ├── Claude: markdown conversation files
    └── Gemini: Google Takeout JSON

System does:
├── Parse resume → extract career timeline, skills, roles
├── Parse AI exports → segment conversations by topic
├── Filter → keep only professional/behavioral content
├── Extract → identify stories, decisions, patterns
├── Embed → store in vector database
└── Build → unified personal memory profile
```

### Phase 2: Gap Detection + Memory Improvement

```
System analyzes memory profile:
├── Which behavioral categories are covered?
├── Which are missing or weak?
└── What questions would strengthen weak areas?

System suggests questions to user:

[MNEMIX]: Your profile has strong technical stories
           but I found gaps in:
           - Conflict resolution (0 stories)
           - Handling failure (1 story — needs more)
           
           Let me ask you some questions to fill these.
           
           Tell me about a time a colleague disagreed
           with your technical approach. What happened?

[USER]:   Types their answer...

[MNEMIX]: Saved. Tagged: conflict_resolution, technical_leadership
           Memory profile updated. Gap partially filled.
```

### Phase 3: Mock Interview

```
System acts as AI interviewer:

[MNEMIX — INTERVIEWER]:
Session: Software Engineer Behavioral Interview
Company type: Product startup
Duration: ~30 minutes
Questions: 8

Ready? Press ENTER to begin.

---

Question 1/8:
Tell me about the most complex technical problem
you have solved in the last 12 months.
Take your time.

[Your answer]:
> Types answer...

[MNEMIX]: Answer recorded. Moving to next question.

---

Question 2/8:
Describe a situation where you had to push back
on a product requirement. How did you handle it?

[Your answer]:
> Types answer...

[Continue through all 8 questions]
```

### Phase 4: Silent Evaluation + Feedback

```
After all questions answered:

[MNEMIX — EVALUATION REPORT]
═══════════════════════════════════════════════

OVERALL SCORE: 74/100

QUESTION 1: Complex technical problem
Your answer: [summary]
Memory match: STRONG — referenced actual Veda project ✅
Specificity: HIGH — named real technology ✅
Outcome stated: YES — "corrupting user data fixed" ✅
What was missing: Quantify the impact
                  ("affected X users" or "took Y hours")
Suggested improvement:
"Add: 'This affected approximately 3,000 active users
 and took 6 hours to fully remediate including
 data recovery.' Numbers make stories credible."

─────────────────────────────────────────────────

QUESTION 2: Pushing back on requirement
Your answer: [summary]
Memory match: WEAK — generic answer, no specific story ⚠️
Specificity: LOW — no project or person named ❌
Outcome stated: NO ❌
What was missing: A real story from your history.
                  I found a relevant memory you didn't use:
                  "Disagreed with client on Django vs FastAPI
                   architecture at BluHat — presented data
                   and convinced them."
Suggested improvement:
"Use the BluHat architecture story. It directly
 answers this question and you lived it."

─────────────────────────────────────────────────

PATTERNS OBSERVED:
✅ Strong: Technical specificity, real project references
⚠️  Weak: Quantifying outcomes with numbers
❌  Missing: Using conflict/pushback stories you have

NEXT SESSION RECOMMENDATION:
Practice: "Influence without authority" questions
Build: 2 more stories with quantified outcomes
Review: Your conflict memories before next session

═══════════════════════════════════════════════
```

---

## 4. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MNEMIX SYSTEM                        │
│                                                         │
│  ┌──────────────┐    ┌───────────────────────────────┐  │
│  │   INGESTION  │    │      PERSONAL MEMORY ENGINE   │  │
│  │    LAYER     │    │                               │  │
│  │              │    │  ┌─────────┐  ┌────────────┐  │  │
│  │ Resume PDF   │───▶│  │ Filter  │  │  Extract   │  │  │
│  │ ChatGPT ZIP  │    │  │ Engine  │─▶│  Engine    │  │  │
│  │ Claude MD    │    │  └─────────┘  └─────┬──────┘  │  │
│  │ Gemini JSON  │    │                     │         │  │
│  └──────────────┘    │               ┌─────▼──────┐  │  │
│                      │               │  pgvector  │  │  │
│  ┌──────────────┐    │               │   Memory   │  │  │
│  │  INTERVIEW   │    │               │    Store   │  │  │
│  │    ENGINE    │    │               └─────┬──────┘  │  │
│  │              │    │                     │         │  │
│  │ Q Generator  │◀───┤               ┌─────▼──────┐  │  │
│  │ Answer Eval  │    │               │  Retrieval │  │  │
│  │ Gap Detector │    │               │    API     │  │  │
│  │ Feedback Gen │    │               └────────────┘  │  │
│  └──────────────┘    └───────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │            SELF-IMPROVEMENT ENGINE               │   │
│  │                                                  │   │
│  │  Interview transcripts → Pattern learning        │   │
│  │  Question effectiveness → Q quality improvement  │   │
│  │  Cross-user signals → Better new user defaults   │   │
│  │  Field-specific → Domain question banks          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              TERMINAL INTERFACE                  │   │
│  │         (API-first, UI-ready design)             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
INGESTION FLOW:
Raw documents
    → Segmentation (split by topic, time)
    → Classification (professional / personal / behavioral)
    → Extraction (LLM: identify memories)
    → Embedding (text → vectors)
    → Storage (pgvector + PostgreSQL)
    → Gap analysis (what's missing?)
    → Question suggestions (fill the gaps)

INTERVIEW FLOW:
User starts session
    → Load user memory profile into RAM
    → Pre-generate top 20 questions for their profile
    → Cache in Redis
    → Present questions one by one
    → Collect answers silently
    → End of session: evaluate all answers together
    → Generate structured feedback report
    → Save session to database
    → Update self-improvement engine

SELF-IMPROVEMENT FLOW:
Interview session saved
    → Extract question-answer pairs
    → Evaluate what worked / didn't
    → Update question effectiveness scores
    → Identify patterns across users in same field
    → Update global question bank
    → Improve new user defaults
```

---

## 5. The Two Core Engines

### Engine 1: Personal Memory Engine

This engine takes raw documents and builds a structured, searchable memory profile for each user.

#### 5.1 Ingestion Pipeline

```
STEP 1: Document Parsing

Resume (PDF):
→ Extract: name, roles, companies, dates, skills, projects
→ Tool: PyMuPDF (free, local, fast)
→ Output: structured JSON

ChatGPT Export (conversations.json):
→ Extract: all user messages only (skip GPT responses)
→ Filter: messages > 20 words (too short = noise)
→ Group: by conversation
→ Output: list of conversation segments

Claude Export (markdown files):
→ Extract: user turns from markdown
→ Parse: [Human] tags
→ Output: list of conversation segments

Gemini Export (Google Takeout JSON):
→ Extract: user messages
→ Output: list of conversation segments

STEP 2: Conversation Segmentation

Problem: One ChatGPT conversation can span 10 topics
Solution: Split by topic shift + time gap

Split triggers:
├── Time gap > 24 hours between messages
├── Topic shift (embedding distance > 0.5)
└── Explicit topic change ("different question", "anyway")

Result: Small, coherent topic segments
        Each segment = one topic = one classification unit

STEP 3: Classification

For each segment → classify into:
├── PROFESSIONAL     → process for memories
├── BEHAVIORAL_PRO   → process for behavioral stories
├── MIXED            → extract only professional sentences
└── PERSONAL         → skip entirely

Classifier: Rule-based first (free, fast)
            Haiku for ambiguous cases (~200ms, cheap)

Rule-based signals:

PROFESSIONAL keywords (auto-accept):
"API", "database", "bug", "deploy", "client", "sprint",
"architecture", "team", "deadline", "code review",
"production", "migration", "performance", "system"

PERSONAL keywords (auto-reject):
"recipe", "movie", "fitness", "relationship", "travel",
"birthday", "medical", "religion", "politics", "game"

BEHAVIORAL_PRO indicators (send to Haiku):
"I tend to", "I've realized", "I struggle with",
"my manager", "my team", "at work", "in my career"

STEP 4: Memory Extraction

For classified professional/behavioral segments:
Send to LLM with extraction prompt
Output: structured memory objects

Memory Object:
{
  "content": "Led Django to FastAPI migration,
              reduced API latency by 40%",
  "category": "technical_achievement",
  "themes": ["backend", "performance", "leadership"],
  "interview_questions": [
    "Tell me about a technical challenge you solved",
    "What is your biggest professional achievement"
  ],
  "confidence": 0.91,
  "source": "chatgpt_export",
  "date_context": "2023",
  "has_outcome": true,
  "outcome_quantified": true
}

STEP 5: Embedding + Storage

Embed each memory → 1536-dim vector
Store in pgvector table
Index: HNSW (fast approximate search)
Retrieval: cosine similarity

STEP 6: Profile Building

After all memories extracted:
Run profile synthesis pass (Sonnet — one time, quality needed)

Profile includes:
├── Communication style
│   (direct/verbose, uses metrics?, vocabulary patterns)
├── Strength areas (categories with 3+ strong stories)
├── Gap areas (categories with 0-1 weak stories)
├── Career narrative (3-sentence professional summary)
├── Technical fingerprint (verified stack from code examples)
└── Behavioral fingerprint (how they handle pressure, conflict)
```

#### 5.2 Gap Detection + Suggested Questions

```python
# Gap categories for IT professionals

REQUIRED_CATEGORIES = {
    # Behavioral
    "leadership":           {"minimum": 3, "weight": "high"},
    "conflict_resolution":  {"minimum": 2, "weight": "high"},
    "failure_learning":     {"minimum": 2, "weight": "high"},
    "technical_achievement":{"minimum": 3, "weight": "high"},
    "collaboration":        {"minimum": 2, "weight": "medium"},
    "ambiguity_handling":   {"minimum": 2, "weight": "medium"},
    "initiative":           {"minimum": 2, "weight": "medium"},
    
    # Technical
    "system_design":        {"minimum": 1, "weight": "high"},
    "debugging":            {"minimum": 2, "weight": "medium"},
    "tech_decisions":       {"minimum": 2, "weight": "high"},
    "performance":          {"minimum": 1, "weight": "medium"},
    
    # Identity
    "career_goals":         {"minimum": 1, "weight": "medium"},
    "values":               {"minimum": 1, "weight": "low"},
    "strengths":            {"minimum": 2, "weight": "medium"}
}

def detect_gaps(user_profile):
    gaps = []
    for category, config in REQUIRED_CATEGORIES.items():
        count = user_profile.count_memories(category)
        if count < config["minimum"]:
            gaps.append({
                "category": category,
                "have": count,
                "need": config["minimum"],
                "priority": config["weight"],
                "suggested_question": generate_gap_question(
                    category, user_profile
                )
            })
    return sorted(gaps, key=lambda x: x["priority"])
```

---

### Engine 2: Interview Engine

This engine conducts realistic mock interviews and evaluates performance.

#### 5.3 Question Generation

```
Question sources (in priority order):

1. Global Question Bank (self-improvement engine builds this)
   Pre-vetted, field-specific, effectiveness-scored
   Always current with real interview trends
   
2. User-specific questions (generated from gaps)
   "User has no conflict stories → ask conflict question"
   
3. Memory-triggered questions
   System sees a strong memory → asks about it
   "User has a race condition story → 
    'Tell me about a critical bug you fixed'"

Question selection algorithm:

def select_questions(user_profile, session_config):
    questions = []
    
    # Always include: tell me about yourself
    questions.append(UNIVERSAL_OPENER)
    
    # Cover strength areas (2-3 questions)
    # → Let user shine on what they know well
    strength_qs = get_strength_questions(user_profile)
    questions.extend(strength_qs[:2])
    
    # Cover gap areas (2-3 questions)
    # → Expose weaknesses for feedback
    gap_qs = get_gap_questions(user_profile)
    questions.extend(gap_qs[:2])
    
    # Field-specific technical (2 questions)
    tech_qs = get_technical_questions(
        user_profile.primary_stack,
        user_profile.seniority_level
    )
    questions.extend(tech_qs[:2])
    
    # Random from global bank (1 question)
    # → Unpredictability, like real interviews
    questions.append(get_random_question(user_profile.field))
    
    # Shuffle middle questions (keep opener fixed)
    middle = questions[1:]
    random.shuffle(middle)
    return [questions[0]] + middle[:7]  # 8 total
```

#### 5.4 Answer Collection

```
Terminal flow:

[MNEMIX]: Question 3/8
          ─────────────────────────────────────
          Tell me about a time you had to make
          a technical decision under pressure.
          
          Take your time. Type your answer below.
          Press ENTER twice when done.
          ─────────────────────────────────────

[USER]:   > We were 2 days before a product launch
            and discovered our PostgreSQL queries
            were timing out under load...
            
          > [ENTER ENTER]

[MNEMIX]: Got it. Next question in 3 seconds...

System does silently:
├── Store answer with timestamp
├── Note: answer length, keywords used
├── Note: did they reference a specific project?
├── Note: did they quantify the outcome?
└── Continue to next question
```

#### 5.5 Silent Evaluation Engine

```
After session ends, evaluate ALL answers together:

For each answer, check:

1. MEMORY MATCH
   Did user reference a real memory from their profile?
   Method: Embed answer → similarity search against memories
   Score: 0-3 (0=generic, 3=strongly grounded in real memory)

2. SPECIFICITY
   Did answer include specific details?
   Signals: project names, technology names, people roles,
            numbers, dates, company names
   Score: 0-3

3. OUTCOME STATED
   Did user describe what happened as a result?
   Signals: "resulted in", "led to", "we achieved",
            "the outcome was", "which meant"
   Score: 0-1 (binary)

4. OUTCOME QUANTIFIED
   Did outcome include a number?
   Signals: percentages, time durations, user counts,
            revenue figures, performance improvements
   Score: 0-1 (binary)

5. MEMORY OPPORTUNITY MISSED
   Did user give generic answer when they had a
   relevant specific story they didn't use?
   Method: Retrieve top memories for this question
           Compare to what they actually said
           Flag if similarity < 0.4 (they ignored their stories)

6. ANSWER COHERENCE
   Is the answer structured? (Situation → Action → Result)
   Is it the right length? (not too short, not too long)
   Score: 0-2

TOTAL SCORE per answer: 0-11 points
Normalized to 0-100 for display

OVERALL SCORE: Average across all answers
```

#### 5.6 Feedback Generation

```
After evaluation, generate feedback report:

Structure:
├── Overall score + one-line verdict
├── Per-question breakdown
│   ├── What you said (2-sentence summary)
│   ├── What worked
│   ├── What was missing
│   ├── Memory you could have used (if missed)
│   └── Exact suggested improvement
├── Pattern analysis across all answers
│   ├── Consistent strengths
│   ├── Consistent weaknesses
│   └── Most important thing to fix before next interview
└── Next session recommendation
    ├── Topics to practice
    ├── Stories to build
    └── Questions to prepare

Model for feedback: Claude Sonnet 4.6
Reason: Feedback quality is user-facing and high-stakes
        Generic feedback = useless
        Sonnet quality = specific, actionable, encouraging
```

---

## 6. The Self-Improvement Engine

This is MNEMIX's most important long-term differentiator.

### 6.1 What It Does

```
Every interview session generates:
├── Questions asked
├── User answers (anonymized)
├── Evaluation scores
├── Which questions got the best answers
├── Which questions consistently get poor answers
├── Which memory categories were most useful
└── Field + seniority context

The self-improvement engine processes this across ALL users:
├── Identifies high-effectiveness questions
│   (questions that surface genuine stories)
├── Identifies low-effectiveness questions
│   (questions that get generic non-answers)
├── Builds field-specific question banks
│   (SWE questions vs data engineer vs PM)
├── Learns seniority calibration
│   (senior IC vs manager vs junior dev)
└── Identifies new interview patterns
    (as interview formats evolve, system detects it)
```

### 6.2 Interview Transcript Learning

```
You specifically mentioned:
"Our system needs to handle interview transcriptions
 since all users' interviews are already transcribed."

This is the most powerful learning signal available.

Real interview transcripts contain:
├── Actual questions real interviewers ask
│   (not what prep guides say they ask)
├── What follow-up questions came after each answer
├── What signals interviewers probed on
├── Interview format patterns by company type
└── What answers led to offers vs rejections
    (if user reports outcome)

Processing flow:

User submits transcript:
1. Parse → extract Q&A pairs
2. Identify: company type, role level, interview stage
3. Extract: unique/interesting questions not in bank
4. Score: question novelty vs existing bank
5. If novel + high quality → add to global bank
6. Update: question frequency by field + company type

Over time:
Month 1:  100 transcripts → 500 real questions
Month 3:  1000 transcripts → 2000 real questions
Month 6:  5000 transcripts → field-specific banks
           "SWE at product startup → top 50 questions"
           "Data engineer at FAANG → top 30 questions"
           "PM at early-stage startup → top 40 questions"

This creates a moat no competitor can buy:
Real interview questions from real interviews
Continuously updated as interview trends change
Personalized by field, seniority, company type
```

### 6.3 New User Bootstrapping

```
Problem: New user joins with no AI history
         Memory profile is empty
         Interview quality is poor

Solution: Use cross-user learning

For a new user who declares:
Field: Software Engineering
Seniority: Mid-level (3-5 years)
Stack: Python, FastAPI, PostgreSQL
Target: Product startups

System does:
├── Pull top questions for this profile from global bank
├── Pull common gap areas for this profile type
│   (mid-level SWEs typically lack: conflict stories,
│    system design at scale, stakeholder management)
├── Generate targeted questions to fill those gaps
└── Start interview with field-calibrated questions
    even before any personal memory exists

Result: New user gets a useful experience from day 1
        Not a blank slate experience
        System improves as their memory fills in
```

### 6.4 Question Effectiveness Scoring

```python
class QuestionEffectivenessTracker:
    
    def update_score(self, question_id: str, 
                     answer_quality: float,
                     field: str,
                     seniority: str):
        """
        Called after every interview session
        Updates rolling average effectiveness per question
        """
        
        # Bayesian update — new evidence weighted by confidence
        current = self.get_score(question_id, field, seniority)
        
        updated_score = (
            current.score * current.weight +
            answer_quality * 1.0
        ) / (current.weight + 1.0)
        
        self.save_score(
            question_id=question_id,
            field=field,
            seniority=seniority,
            score=updated_score,
            weight=current.weight + 1.0
        )
    
    def get_best_questions(self, field: str, 
                            seniority: str,
                            category: str,
                            limit: int = 5) -> list[Question]:
        """
        Returns highest-effectiveness questions for context
        Questions that consistently surface good stories
        """
        return self.db.query("""
            SELECT q.*, qe.score
            FROM questions q
            JOIN question_effectiveness qe 
                ON q.id = qe.question_id
            WHERE qe.field = $1
            AND qe.seniority = $2
            AND q.category = $3
            AND qe.weight >= 5  -- at least 5 data points
            ORDER BY qe.score DESC
            LIMIT $4
        """, field, seniority, category, limit)
```

---

## 7. Latency Strategy

### 7.1 The Latency Problem

```
Standard pipeline (everyone else):
User submits answer → wait → wait → wait → feedback

MNEMIX target:
Demo (v0.1): < 3 seconds for question generation
             < 5 seconds for feedback report
Real product: < 500ms question display
              < 1 second first feedback token (streaming)
```

### 7.2 Pre-Generation Cache

```
Most powerful latency technique in the system.

On session start (before first question appears):
1. Load user memory profile into RAM
2. Determine session question set (8 questions)
3. Pre-generate ALL 8 questions with context (~3-5 seconds)
   Run in PARALLEL — all 8 at once, not sequential
4. Cache in Redis with session TTL
5. Present first question: instant (Redis hit = ~1ms)

User experience:
Press ENTER to start → 3-5 second pause (pre-generation)
→ "Preparing your personalized interview..."
First question appears instantly
All subsequent questions: instant

vs competitors:
ParakeetAI: generates each answer on-demand (~3-5 seconds each)
MNEMIX: generates all upfront once (~4 seconds total)
         then each question: instant
```

### 7.3 Parallel Processing

```python
async def pre_generate_session(user_profile, questions):
    """
    Generate all questions simultaneously
    Not one by one
    """
    tasks = [
        asyncio.create_task(
            generate_question_context(q, user_profile)
        )
        for q in questions
    ]
    
    # All 8 run simultaneously
    # Total time = slowest single question (~3-4 seconds)
    # NOT 8 × 3 = 24 seconds
    results = await asyncio.gather(*tasks)
    
    return results
```

### 7.4 Model Selection for Latency

```
Question generation (pre-computed, speed less critical):
→ GPT-4.1 mini or Gemini 2.5 Flash
→ Quality + cost balance

Memory retrieval (per question, latency critical):
→ pgvector HNSW index (< 10ms for 1000 memories)
→ RAM session cache (< 5ms)

Answer evaluation (after session, not real-time):
→ Claude Sonnet 4.6
→ Quality over speed — user waits for full report
→ Target: < 10 seconds for full evaluation

Feedback generation (after evaluation):
→ Claude Sonnet 4.6 streaming
→ User sees feedback appearing word by word
→ Psychological latency much better than batch wait

Classification (background, cheap):
→ Rule-based Python (< 1ms)
→ Haiku only for ambiguous cases
```

### 7.5 Demo vs Production Latency Targets

```
DEMO (v0.1 — terminal, local):
├── Session start → first question: < 5 seconds
├── Between questions: 3 second countdown (pre-loaded)
├── All answers → evaluation start: instant
├── Evaluation → feedback: < 15 seconds
└── Acceptable for demo/testing

PRODUCTION (with streaming UI):
├── Session start → first question: < 2 seconds
├── Between questions: < 500ms (pre-generated)
├── Feedback: streaming (first word < 1 second)
└── Feels instant to user
```

---

## 8. Data Schema

### Core Tables

```sql
-- Users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    field           VARCHAR(50),    -- software_engineering, etc.
    seniority       VARCHAR(20),    -- junior, mid, senior, lead
    primary_stack   TEXT[],         -- ["Python", "FastAPI", "PostgreSQL"]
    target_roles    TEXT[]          -- ["SWE", "Backend Engineer"]
);

-- Memory Store
CREATE TABLE memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    category        VARCHAR(50),
    themes          TEXT[],
    interview_qs    TEXT[],         -- which questions this answers
    confidence      FLOAT,
    source          VARCHAR(50),    -- resume, chatgpt, claude, manual
    date_context    VARCHAR(20),
    has_outcome     BOOLEAN DEFAULT false,
    outcome_quant   BOOLEAN DEFAULT false,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    access_count    INTEGER DEFAULT 0,
    last_accessed   TIMESTAMPTZ
);
CREATE INDEX ON memories USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON memories (user_id, category);

-- User Profile
CREATE TABLE user_profiles (
    user_id         UUID PRIMARY KEY REFERENCES users(id),
    communication_style JSONB,
    strength_areas  TEXT[],
    gap_areas       TEXT[],
    career_narrative TEXT,
    tech_fingerprint TEXT[],
    behavioral_fp   JSONB,
    last_updated    TIMESTAMPTZ DEFAULT NOW()
);

-- Global Question Bank (self-improvement engine)
CREATE TABLE questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text            TEXT NOT NULL,
    category        VARCHAR(50),
    field           VARCHAR(50),    -- null = universal
    seniority       VARCHAR(20),    -- null = all levels
    source          VARCHAR(50),    -- generated, transcript, manual
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Question Effectiveness (self-improvement engine)
CREATE TABLE question_effectiveness (
    question_id     UUID REFERENCES questions(id),
    field           VARCHAR(50),
    seniority       VARCHAR(20),
    score           FLOAT DEFAULT 0.5,
    weight          FLOAT DEFAULT 0.0,  -- number of data points
    PRIMARY KEY (question_id, field, seniority)
);

-- Interview Sessions
CREATE TABLE interview_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    session_type    VARCHAR(50),    -- behavioral, technical, mixed
    overall_score   FLOAT,
    questions_asked UUID[],
    status          VARCHAR(20) DEFAULT 'in_progress'
);

-- Session Q&A
CREATE TABLE session_answers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES interview_sessions(id),
    question_id     UUID REFERENCES questions(id),
    question_text   TEXT,
    answer_text     TEXT,
    answer_order    INTEGER,
    memory_match_score    FLOAT,
    specificity_score     FLOAT,
    outcome_stated        BOOLEAN,
    outcome_quantified    BOOLEAN,
    memory_opportunity    UUID,   -- memory they could have used
    total_score           FLOAT,
    feedback_text         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Interview Transcripts (self-improvement engine)
CREATE TABLE interview_transcripts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    raw_transcript  TEXT,
    company_type    VARCHAR(50),
    role_level      VARCHAR(20),
    interview_stage VARCHAR(50),    -- screen, technical, final
    outcome         VARCHAR(20),    -- offer, reject, unknown
    processed       BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Extracted Questions from Transcripts
CREATE TABLE transcript_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id   UUID REFERENCES interview_transcripts(id),
    question_text   TEXT,
    category        VARCHAR(50),
    novelty_score   FLOAT,
    added_to_bank   BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Ingestion Jobs
CREATE TABLE ingestion_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    source_type     VARCHAR(50),    -- resume, chatgpt, claude, gemini
    status          VARCHAR(20) DEFAULT 'pending',
    total_segments  INTEGER,
    processed       INTEGER DEFAULT 0,
    memories_found  INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT
);
```

---

## 9. API Design

All endpoints designed API-first. Terminal uses these same endpoints. UI will use these same endpoints. Nothing changes when UI is added.

### Ingestion APIs

```
POST   /api/v1/ingest/resume
       Body: multipart/form-data (PDF file)
       Returns: {job_id, status, message}

POST   /api/v1/ingest/ai-export
       Body: multipart/form-data (ZIP file), source_type
       Returns: {job_id, status, message}

GET    /api/v1/ingest/status/{job_id}
       Returns: {status, progress_percent, memories_found}

GET    /api/v1/memory/profile
       Returns: full memory profile for user

GET    /api/v1/memory/gaps
       Returns: list of gaps with suggested questions

POST   /api/v1/memory/add
       Body: {content, category, themes}
       Returns: {memory_id, saved: true}

POST   /api/v1/memory/answer-gap-question
       Body: {question_id, answer_text}
       Returns: {memory_id, saved: true, gap_filled: bool}
```

### Interview APIs

```
POST   /api/v1/interview/start
       Body: {session_type, num_questions}
       Returns: {session_id, first_question, question_number}

POST   /api/v1/interview/answer
       Body: {session_id, question_id, answer_text}
       Returns: {next_question, question_number} 
                OR {session_complete: true}

GET    /api/v1/interview/evaluate/{session_id}
       Returns: full evaluation + feedback report

GET    /api/v1/interview/sessions
       Returns: list of past sessions with scores
```

### Self-Improvement APIs

```
POST   /api/v1/transcript/submit
       Body: {raw_transcript, company_type, role_level,
              interview_stage, outcome}
       Returns: {transcript_id, questions_extracted}

GET    /api/v1/questions/bank
       Query params: field, seniority, category, limit
       Returns: list of questions sorted by effectiveness

POST   /api/v1/feedback/question
       Body: {question_id, was_effective, notes}
       Returns: {updated: true}
```

### System APIs

```
GET    /api/v1/health
GET    /api/v1/health/db
GET    /api/v1/health/redis
GET    /api/v1/system/stats
       Returns: {total_users, total_memories, 
                  total_sessions, questions_in_bank}
```

---

## 10. Build Plan — Demo v0.1

### What v0.1 Includes

```
IN SCOPE (2 days, terminal only):
✅ Resume PDF ingestion → memory extraction
✅ ChatGPT/Claude/Gemini export parsing
✅ Memory profile building
✅ Gap detection + suggested questions
✅ Gap filling via terminal Q&A
✅ Mock interview session (8 questions)
✅ Silent evaluation of all answers
✅ Feedback report generation
✅ Basic question bank (50 pre-seeded questions)
✅ Interview transcript submission
✅ Basic self-improvement (score tracking)

OUT OF SCOPE for v0.1:
❌ UI (terminal only)
❌ Authentication (single user local)
❌ Redis caching (local SQLite instead)
❌ Production deployment
❌ Multiple users
❌ Real-time streaming in terminal
```

### Project Structure

```
mnemix/
├── main.py                    # FastAPI app entry point
├── cli.py                     # Terminal interface (typer)
├── config.py                  # Settings, API keys, paths
│
├── api/
│   ├── __init__.py
│   ├── ingest.py              # Ingestion endpoints
│   ├── memory.py              # Memory endpoints
│   ├── interview.py           # Interview endpoints
│   └── transcript.py          # Transcript endpoints
│
├── core/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── resume_parser.py   # PDF → structured data
│   │   ├── chatgpt_parser.py  # conversations.json parser
│   │   ├── claude_parser.py   # markdown files parser
│   │   └── gemini_parser.py   # Google Takeout parser
│   │
│   ├── processing/
│   │   ├── segmenter.py       # Split conversations by topic
│   │   ├── classifier.py      # Professional vs personal
│   │   └── extractor.py       # LLM memory extraction
│   │
│   ├── memory/
│   │   ├── store.py           # pgvector operations
│   │   ├── retriever.py       # Semantic search
│   │   └── gap_detector.py    # Gap analysis
│   │
│   ├── interview/
│   │   ├── session.py         # Session management
│   │   ├── question_gen.py    # Question selection
│   │   ├── evaluator.py       # Silent evaluation
│   │   └── feedback_gen.py    # Feedback generation
│   │
│   └── self_improvement/
│       ├── transcript_proc.py # Process submitted transcripts
│       ├── question_bank.py   # Question bank management
│       └── effectiveness.py   # Score tracking
│
├── models/
│   ├── __init__.py
│   ├── memory.py              # Pydantic schemas
│   ├── interview.py
│   └── user.py
│
├── db/
│   ├── __init__.py
│   ├── connection.py          # Database connection
│   └── migrations/            # SQL migration files
│       └── 001_initial.sql
│
├── llm/
│   ├── __init__.py
│   ├── router.py              # Model selection logic
│   ├── prompts.py             # All system prompts
│   └── embeddings.py         # Embedding generation
│
├── tests/
│   ├── test_parsers.py
│   ├── test_classifier.py
│   └── test_interview.py
│
├── data/
│   └── question_bank_seed.json  # 50 pre-seeded questions
│
├── .env.example
├── requirements.txt
└── README.md
```

### Day 1 Build Targets

```
Morning (4 hours):
├── Project setup (FastAPI + database + Supabase pgvector)
├── Resume PDF parser (PyMuPDF)
├── ChatGPT JSON parser
├── Claude markdown parser
└── Basic rule-based classifier

Afternoon (4 hours):
├── LLM extraction pipeline (GPT-4.1 mini)
├── Embedding generation + pgvector storage
├── Memory profile builder
└── Gap detection logic

Evening (2 hours):
├── Basic API endpoints (ingest, memory)
├── Test ingestion with your own resume
└── Verify memories are extracted correctly
```

### Day 2 Build Targets

```
Morning (4 hours):
├── Question bank seeding (50 questions)
├── Question selection algorithm
├── Interview session management
└── Terminal interview flow (Typer CLI)

Afternoon (4 hours):
├── Answer collection + storage
├── Silent evaluation engine
├── Feedback generation (Sonnet)
└── Terminal feedback display

Evening (2 hours):
├── Transcript submission endpoint
├── Basic effectiveness scoring
├── End-to-end test: ingest → interview → feedback
└── Fix bugs from testing
```

### Technology Stack (Demo)

```
Backend:
├── FastAPI              — API framework
├── Typer                — Terminal CLI interface
├── SQLite (local)       — Database for demo
│   → Supabase pgvector for production
├── sentence-transformers — Local embeddings (free)
│   → OpenAI embeddings for production
└── PyMuPDF              — PDF parsing (free, local)

AI Models:
├── Extraction:          GPT-4.1 mini ($0.40/M)
├── Classification:      Rule-based Python (free)
│   + GPT-4.1 mini for ambiguous (~10% of cases)
├── Profile building:    Claude Sonnet 4.6 (one-time)
├── Question generation: GPT-4.1 mini
├── Feedback:            Claude Sonnet 4.6
└── Embeddings:          sentence-transformers local (free)
    → all-MiniLM-L6-v2 (384-dim, good enough for demo)

Local only — no Redis, no cloud, no deployment needed.
```

### Estimated API Costs for Demo Testing

```
Your personal testing session:

Resume parsing: ~2,000 tokens → $0.001
ChatGPT export (500K tokens input):
  → Classification: 20% sent to Haiku → $0.04
  → Extraction: 15% sent to mini → $0.03
Profile building: ~8,000 tokens Sonnet → $0.024
Question generation: 8 × 500 tokens → $0.002
Evaluation + feedback: ~3,000 tokens Sonnet → $0.009

Total for one full test cycle: ~$0.11 (₹9)

Your 3 friends testing:
Total: ~$0.45 (₹38)

Budget required for demo phase: ₹500 (generous buffer)
This is entirely affordable even without income.
```

---

## 11. Technology Stack (Full Production)

```
Layer               Technology              Why
────────────────────────────────────────────────────────────
API Framework       FastAPI                 Your strength
Database            Supabase (PostgreSQL)   Your stack
Vector Store        pgvector on Supabase    Your stack
Cache               Upstash Redis           Serverless, cheap
Background Jobs     Celery + Upstash Redis  Your stack
Embeddings          OpenAI text-embed-3-small Best quality/cost
STT (future)        Deepgram                Fastest streaming

AI Models:
├── Classification   Rule-based + Gemini Flash  Fast, cheap
├── Extraction       GPT-4.1 mini               Best JSON output
├── Profile Build    Claude Sonnet 4.6           Best quality
├── Q Generation     GPT-4.1 mini               Fast, good
├── Evaluation       Claude Sonnet 4.6           Best reasoning
├── Feedback         Claude Sonnet 4.6           Best writing
└── Gap Analysis     Kimi K2 Thinking            Best reasoning/cost

Model Access        OpenRouter              One API, all models
Deployment          Railway                 Your familiarity
Frontend (future)   Next.js 14              Your stack
Payments            Razorpay + Stripe       INR + international
```

---

## 12. Cost Model

### Per-User Economics

```
ONBOARDING (one-time per user):
├── Resume parsing:           $0.001
├── AI export processing:     $0.05 - 0.20
├── Profile building:         $0.03
└── Total onboarding:         $0.08 - 0.25

PER INTERVIEW SESSION:
├── Question generation:      $0.002
├── Evaluation:               $0.015
├── Feedback generation:      $0.025
└── Total per session:        $0.04

MONTHLY (active user, 8 sessions/month):
├── Onboarding (amortized):   $0.02
├── Interview sessions:       $0.32
├── Gap detection:            $0.02
└── Total monthly API cost:   ~$0.36 (₹30)

YOUR PRICING:
Free tier: 3 sessions (validate value)
Starter:   ₹299/month (10 sessions)
Pro:       ₹599/month (unlimited)
Credits:   ₹49/session (no subscription)

GROSS MARGIN:
Pro user: ₹599 revenue - ₹30 cost = ₹569 margin (95%)
Even 50% API cost error: still 90% margin
This is exceptional SaaS economics.
```

---

## 13. Roadmap

### Demo v0.1 (2 days — terminal only)
```
✅ Resume + AI export ingestion
✅ Memory extraction + profile building
✅ Gap detection + suggested questions
✅ Gap filling via conversation
✅ Mock interview (terminal)
✅ Silent evaluation + feedback
✅ Basic self-improvement (score tracking)
```

### v0.2 (1 week — friend testing)
```
→ Simple web UI (Next.js)
→ File upload interface
→ Memory profile viewer
→ Interview in browser (text-based)
→ Feedback displayed in UI
→ Multiple user support (basic auth)
```

### v0.3 (2 weeks — public beta)
```
→ User accounts + authentication
→ Razorpay payment integration
→ Credit-based pricing (₹49/session)
→ Redis caching (pre-generation)
→ Streaming feedback output
→ Session history
```

### v1.0 (Month 2 — launch)
```
→ Full personalization pipeline
→ Company-specific preparation mode
→ Transcript submission (self-improvement)
→ Creator/affiliate program
→ Landing page + comparison pages (SEO)
→ Mobile-optimized web
```

### v2.0 (Month 4 — scale)
```
→ Voice input (Deepgram STT)
→ Chrome extension (coding interviews)
→ Phone as second screen mode
→ API for third-party integration
→ Enterprise/bootcamp B2B tier
```

---

## 14. Investor Narrative

### The One-Paragraph Pitch

> MNEMIX is building the personal memory layer that makes AI interview tools actually work. Every existing tool — ParakeetAI ($1.8M ARR), LockedIn AI ($770K), Final Round AI ($6.88M raised) — gives generic answers because they start from a resume. MNEMIX starts from two years of your real AI conversation history, your actual projects, your genuine communication style. The answers sound like you because they are you. We're building on a technical moat nobody has touched, in a proven market with growing urgency, and the self-improvement engine means we get smarter with every user who interviews.

### The Numbers That Matter

```
Market:
├── Global AI interview tool market: $150M+ and growing
├── ParakeetAI alone: $1.8M ARR, solo founder, 1 year old
├── 35% of candidates now use AI assistance (and growing)
└── Zero tools have personal memory → our entire TAM

Technical moat:
├── Personal memory extraction: nobody has this
├── Self-improvement engine: proprietary question bank
├── Cross-user learning: better for everyone over time
└── Anonymized processing: privacy by design

Unit economics:
├── API cost per active user: ~₹30/month
├── Revenue per Pro user: ₹599/month
├── Gross margin: 95%
└── Payback period: first payment (zero CAC with content)

Traction plan:
├── Week 1: Personal testing + 3 friends
├── Week 2: LinkedIn post + demo video
├── Week 3: 100+ waitlist signups (validation)
├── Month 2: First 50 paying users
└── Month 3: ₹30,000 MRR target
```

### Why Now

```
Three forces converging:

1. AI interviews are mainstream
   35% of candidates already use AI tools
   Market is educated and growing fast

2. The generic answer problem is getting worse
   More AI tools → more generic answers
   Interviewers now expect better → generic fails faster
   Pain is increasing, not decreasing

3. Personal AI history is now exportable
   ChatGPT: full export available
   Claude: full export available
   Gemini: Google Takeout
   2 years of personal context waiting to be unlocked
   Nobody has built the unlock yet

The window to own this category:
6-12 months before funded competitors notice
MNEMIX is building now.
```

### Why This Founder

```
Parth Jetani — Solo founder, full-stack developer

Relevant experience:
├── 3 years building SaaS products (Dynbo, StepGuide)
│   on Google App Engine for US client (BluHat Ventures)
├── Built Veda: WhatsApp AI health coaching bot
│   (FastAPI + Supabase + LLM APIs — production system)
├── Built Cliplift: Video SaaS
│   (Next.js + FastAPI + Stripe/Razorpay + Supabase)
└── Exact stack as MNEMIX: FastAPI, Supabase, LLM APIs

Why this founder for this product:
├── He IS the target user (job hunting, Indian developer)
├── He uses AI daily (deep understanding of the pain)
├── He identified the gap before anyone else documented it
├── He can build the entire v0.1 in 2 days
└── He doesn't need a team to validate — he ships

Competitive advantage:
Solo founder builds 16x more efficiently than teams
(ParakeetAI: $1.8M ARR, solo. LockedIn AI: $770K, 7 people.)
MNEMIX will follow the ParakeetAI playbook:
Ship fast. Distribute aggressively. Build the moat.
```

---

## Appendix: Key Prompts

### Memory Extraction Prompt

```python
EXTRACTION_PROMPT = """
You are extracting interview-relevant professional memories
from a software/tech professional's AI conversation history.

USER'S FIELD: {field}
USER'S ROLE: {role}

Below are USER MESSAGES ONLY from one conversation segment.
Analyze what the user said, not what the AI responded.

Extract ONLY if the user describes their own experience:
1. Professional stories (real situations they handled)
2. Technical decisions they made with reasoning
3. Leadership or team dynamics they navigated
4. Problems they personally solved
5. Career goals or values they expressed
6. Self-reflections about their work patterns

For each extracted memory return:
{
  "content": "One clear sentence describing the memory",
  "category": "technical_achievement|leadership|conflict|
               failure_learning|collaboration|ambiguity|
               initiative|system_design|debugging|
               career_goal|value|strength|working_style",
  "themes": ["max 3 tags"],
  "interview_questions": ["which questions this answers"],
  "confidence": 0.0-1.0,
  "has_outcome": true/false,
  "outcome_quantified": true/false,
  "date_context": "approximate time if mentioned"
}

RULES — strictly follow:
- Extract NOTHING about personal life, health, relationships
- Extract NOTHING the AI said — only what the USER said
- Extract NOTHING that is generic advice without context
- Minimum confidence 0.65 to include
- If no qualifying memories: return {"memories": []}

USER MESSAGES:
{user_messages}

Return valid JSON only. No explanation. No markdown.
"""
```

### Evaluation Prompt

```python
EVALUATION_PROMPT = """
You are evaluating interview answers for a {field} professional
targeting {seniority} level roles.

USER'S MEMORY PROFILE (their real experiences):
{memory_summary}

INTERVIEW QUESTION:
{question}

USER'S ANSWER:
{answer}

MOST RELEVANT MEMORIES FOR THIS QUESTION:
{top_memories}

Evaluate on these dimensions:

1. MEMORY_MATCH (0-3):
   0 = completely generic, no real experience referenced
   1 = vague reference to experience
   2 = clear reference to real project or situation
   3 = specific, named, detailed real experience

2. SPECIFICITY (0-3):
   0 = pure abstraction ("I led a team")
   1 = some specific detail (technology named)
   2 = clear specifics (project, technology, context)
   3 = rich specifics (project, technology, person roles, timeline)

3. OUTCOME_STATED (true/false):
   Did they describe what resulted from their actions?

4. OUTCOME_QUANTIFIED (true/false):
   Did outcome include numbers, percentages, time, or scale?

5. MEMORY_OPPORTUNITY_MISSED (memory_id or null):
   If user gave a generic answer but had a relevant specific
   story they didn't use, provide the memory_id.
   Otherwise null.

6. COHERENCE (0-2):
   0 = rambling, unclear structure
   1 = mostly clear, minor issues
   2 = well-structured, appropriate length

7. SPECIFIC_FEEDBACK (string):
   One actionable suggestion for improving this answer.
   If they missed a memory, mention it specifically.
   If outcome was missing, suggest how to add it.
   Be specific, not generic.

Return JSON only:
{
  "memory_match": 0-3,
  "specificity": 0-3,
  "outcome_stated": bool,
  "outcome_quantified": bool,
  "memory_opportunity_missed": "uuid or null",
  "coherence": 0-2,
  "specific_feedback": "string"
}
"""
```

### Feedback Report Prompt

```python
FEEDBACK_PROMPT = """
You are a senior career coach giving honest, specific
feedback to a {field} professional after a mock interview.

USER PROFILE:
{profile_summary}

SESSION RESULTS:
{all_evaluations}

Generate a structured feedback report.

Tone: Direct, honest, encouraging but not sycophantic.
      Like a respected mentor. Not generic.
      Reference their actual answers and actual memories.

Structure:
1. OVERALL_SCORE: {score}/100
2. ONE_LINE_VERDICT: One honest sentence about their performance
3. QUESTION_FEEDBACK: For each question:
   - what_worked: what was genuinely strong
   - what_was_missing: specific gap
   - memory_suggestion: if they missed a memory, 
     say "You have a story about X that would have 
     answered this perfectly"
   - improvement: exact suggested phrasing if needed
4. PATTERNS:
   - strengths: consistent across answers
   - weaknesses: consistent across answers
   - most_important_fix: the ONE thing that would most
     improve their next interview
5. NEXT_SESSION:
   - practice_topics: list
   - stories_to_build: what memory gaps to fill
   - target_question_types: what to focus on

Return structured text, not JSON.
Format for terminal display.
Use clear section headers.
Be specific. Avoid generic advice.
"""
```

---

*MNEMIX — Built by Parth Jetani*
*"Your interview answers, in your voice, from your real experience."*
*Documentation v1.0 — May 2026*
