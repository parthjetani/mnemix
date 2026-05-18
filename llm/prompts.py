CLASSIFICATION_PROMPT = """You are classifying a conversation segment from a tech professional's AI chat history.

Classify the segment into exactly one category:
- PROFESSIONAL: Technical work, coding, APIs, systems, debugging, deployments, architecture
- BEHAVIORAL_PRO: Work relationships, team dynamics, career reflections, leadership situations, communication at work
- MIXED: Contains both professional and personal content
- PERSONAL: Personal life only — relationships, health, entertainment, food, travel, hobbies

USER MESSAGES:
{user_messages}

Return valid JSON only. No explanation. No markdown fences.
{{"category": "PROFESSIONAL|BEHAVIORAL_PRO|MIXED|PERSONAL", "confidence": 0.0}}"""


EXTRACTION_PROMPT = """You are extracting interview-relevant professional memories from a {field} professional's AI conversation history.

USER'S ROLE: {role}

Below are USER MESSAGES ONLY from one conversation segment. Analyze what the user said about their own experience, not what the AI responded.

Extract ONLY if the user describes:
1. Professional stories — real situations they handled at work
2. Technical decisions they made with reasoning
3. Leadership or team dynamics they navigated
4. Problems they personally solved
5. Career goals or values they expressed
6. Self-reflections about their work patterns

For each extracted memory return:
{{
  "content": "One clear sentence describing the memory (use generic descriptions, no company names or real names)",
  "category": "technical_achievement|leadership|conflict_resolution|failure_learning|collaboration|ambiguity_handling|initiative|communication|pressure_handling|system_design|debugging|tech_decisions|performance_optimization|architecture|career_goal|value|strength|working_style|self_awareness",
  "themes": ["max 3 tags"],
  "interview_qs": ["which standard interview questions this memory answers"],
  "confidence": 0.0,
  "has_outcome": true,
  "outcome_quantified": true,
  "date_context": "approximate time if mentioned, else null"
}}

RULES — strictly follow:
- Extract NOTHING about personal life, health, relationships, entertainment
- Extract NOTHING the AI said — only what the USER said
- Extract NOTHING that is generic advice without personal context
- Minimum confidence 0.65 to include
- Use generic descriptions: "a SaaS startup" not the real company name
- If no qualifying memories: return {{"memories": []}}

USER MESSAGES:
{user_messages}

Return valid JSON only. No explanation. No markdown fences.
{{"memories": []}}"""


PROFILE_PROMPT = """You are synthesizing a professional profile for a {field} engineer based on their extracted memories.

MEMORY SUMMARY (categories and counts):
{memory_summary}

SAMPLE MEMORIES:
{sample_memories}

Synthesize a profile that captures:
1. communication_style: How this person communicates (direct/verbose, data-driven, technical depth)
2. strength_areas: Categories where they have 3+ strong memories
3. gap_areas: Categories with 0-1 memories
4. career_narrative: A 2-sentence professional summary in their voice

Return valid JSON only. No explanation. No markdown fences.
{{
  "communication_style": "description",
  "strength_areas": ["category1", "category2"],
  "gap_areas": ["category1", "category2"],
  "career_narrative": "2-sentence summary"
}}"""


Q_BEHAVIORAL_PROMPT = """Generate one specific behavioral interview question targeting the category: {category}

Context about this candidate:
{profile_summary}

The question must:
- Start with "Tell me about a time..." or "Describe a situation where..."
- Be specific enough to surface a real story
- Be appropriate for a mid-to-senior software/tech professional
- NOT be generic ("Tell me about a challenge") — be specific to the category

Return only the question text. No explanation."""


Q_TECHNICAL_PROMPT = """Generate one specific technical interview question for:
Category: {category}
Tech stack: {stack}
Seniority: {seniority}

The question must:
- Be specific to the listed stack and seniority level
- Test real understanding, not trivia
- Be open-ended enough to allow discussion of trade-offs
- Sound like a real interviewer would ask it

Return only the question text. No explanation."""


EVALUATION_PROMPT = """You are evaluating an interview answer for a {field} professional targeting {seniority}-level roles.

USER'S RELEVANT MEMORIES (their real experiences):
{top_memories}

INTERVIEW QUESTION:
{question}

USER'S ANSWER:
{answer}

Evaluate on these dimensions:

MEMORY_MATCH (0-3):
0 = completely generic, no real experience referenced
1 = vague reference to experience
2 = clear reference to a real project or situation
3 = specific, named, detailed real experience

SPECIFICITY (0-3):
0 = pure abstraction ("I led a team")
1 = some specific detail (technology named)
2 = clear specifics (project, technology, context)
3 = rich specifics (project, tech, roles, timeline, or numbers)

OUTCOME_STATED (true/false): Did they describe what resulted from their actions?

OUTCOME_QUANTIFIED (true/false): Did the outcome include numbers, percentages, time, or scale?

MEMORY_OPPORTUNITY_MISSED (memory_id or null): If the user gave a generic answer but had a relevant specific story they didn't use, provide the memory_id. Otherwise null.

COHERENCE (0-2):
0 = rambling, no clear structure
1 = mostly clear, minor issues
2 = well-structured (situation → action → result), appropriate length

SPECIFIC_FEEDBACK (string): One actionable sentence for improvement. If they missed a memory, mention it. If outcome was missing, say exactly how to add it. Be specific, not generic.

Return valid JSON only. No explanation. No markdown fences.
{{
  "memory_match": 0,
  "specificity": 0,
  "outcome_stated": false,
  "outcome_quantified": false,
  "memory_opportunity_missed": null,
  "coherence": 0,
  "specific_feedback": "string"
}}"""


FEEDBACK_PROMPT = """You are a senior career coach giving honest, specific feedback to a {field} professional after a mock interview.

OVERALL SCORE: {score}/100

USER PROFILE:
{profile_summary}

SESSION RESULTS (all questions and evaluations):
{all_evaluations}

Generate a structured feedback report. Follow this format exactly:

═══════════════════════════════════════════════
MNEMIX INTERVIEW REPORT
═══════════════════════════════════════════════

OVERALL SCORE: {score}/100
VERDICT: [One honest sentence about overall performance]

───────────────────────────────────────────────
PER-QUESTION BREAKDOWN
───────────────────────────────────────────────

[For each question, in order:]
Q[N]: [Question text summary]
What worked: [specific strength from their answer]
What was missing: [specific gap]
[If memory_opportunity_missed: "You have a story about X that would have answered this directly — use it."]
Suggestion: [exact improvement, 1-2 sentences]

───────────────────────────────────────────────
PATTERNS ACROSS ALL ANSWERS
───────────────────────────────────────────────

Consistent strengths: [2-3 bullet points]
Consistent weaknesses: [2-3 bullet points]
Most important fix: [THE single most impactful change for the next interview]

───────────────────────────────────────────────
NEXT SESSION PLAN
───────────────────────────────────────────────

Practice: [list of topic types to work on]
Stories to build: [memory gaps to fill before next session]
Focus questions: [specific question types to practice]

═══════════════════════════════════════════════

Tone: Direct, honest, like a respected mentor. Not sycophantic. Reference their actual answers.
Avoid generic advice. Every sentence should be specific to this session."""


GAP_ANALYSIS_PROMPT = """A tech professional's memory profile has the following gaps in interview coverage:

GAPS (categories below minimum story count):
{gap_categories}

CURRENT MEMORY COUNTS:
{memory_counts}

For each gap category, generate one specific question that would help the user recall and articulate a real story from their experience.

The question must:
- Be direct and specific to the category
- Start with "Tell me about..." or "Describe a time..."
- Help surface a specific real experience, not a hypothetical
- Feel like a natural conversation prompt, not a formal interview question

Return valid JSON only. No explanation. No markdown fences.
{{"gap_questions": [{{"category": "string", "question": "string"}}]}}"""
