from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

MemoryCategory = Literal[
    "leadership", "conflict_resolution", "failure_learning", "technical_achievement",
    "collaboration", "ambiguity_handling", "initiative", "communication", "pressure_handling",
    "system_design", "debugging", "tech_decisions", "performance_optimization", "architecture",
    "career_goal", "value", "strength", "working_style", "self_awareness",
]


# ─── Memory ───────────────────────────────────────────────────────────────────

class MemoryCreate(BaseModel):
    content: str
    category: str
    themes: list[str] = []
    interview_qs: list[str] = []
    confidence: float
    source: str
    date_context: Optional[str] = None
    has_outcome: bool = False
    outcome_quantified: bool = False


class Memory(MemoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: str
    access_count: int = 0
    last_accessed: Optional[str] = None


# ─── Interview Session ─────────────────────────────────────────────────────────

class InterviewSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    started_at: str
    completed_at: Optional[str] = None
    session_type: str
    overall_score: Optional[float] = None
    status: str = "in_progress"
    questions_list: Optional[str] = None


class SessionAnswer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    question_id: str
    question_text: str
    answer_text: Optional[str] = None
    answer_order: int
    memory_match_score: Optional[float] = None
    specificity_score: Optional[float] = None
    outcome_stated: Optional[bool] = None
    outcome_quantified: Optional[bool] = None
    memory_opportunity: Optional[str] = None
    total_score: Optional[float] = None
    feedback_text: Optional[str] = None
    created_at: str


# ─── Question ─────────────────────────────────────────────────────────────────

class Question(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    text: str
    category: str
    field: Optional[str] = None
    seniority: Optional[str] = None
    source: str = "seeded"
    effectiveness_score: float = 0.5
    use_count: int = 0
    created_at: Optional[str] = None


# ─── Ingestion Job ────────────────────────────────────────────────────────────

class IngestionJob(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    status: str = "pending"
    total_segments: int = 0
    processed: int = 0
    memories_found: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


# ─── User Profile ─────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field: str = "software_engineering"
    seniority: str = "mid"
    primary_stack: list[str] = []
    target_roles: list[str] = []
    communication_style: Optional[str] = None
    strength_areas: list[str] = []
    gap_areas: list[str] = []
    career_narrative: Optional[str] = None
    last_updated: Optional[str] = None


# ─── Evaluation ───────────────────────────────────────────────────────────────

class EvaluationResult(BaseModel):
    question_id: str
    question_text: str
    answer_text: str
    memory_match: int           # 0-3
    specificity: int            # 0-3
    outcome_stated: bool
    outcome_quantified: bool
    memory_opportunity_missed: Optional[str] = None
    coherence: int              # 0-2
    specific_feedback: str
    total_score: float          # normalized 0-100


class FeedbackReport(BaseModel):
    session_id: str
    overall_score: float
    report_text: str
    evaluations: list[EvaluationResult]
    session_type: Optional[str] = None
    started_at: Optional[str] = None


# ─── API Request/Response schemas ─────────────────────────────────────────────

class IngestResponse(BaseModel):
    job_id: str
    status: str
    message: str


class MemoryAddRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8_000)
    category: MemoryCategory
    themes: list[str] = Field(default_factory=list, max_length=20)


class InterviewStartRequest(BaseModel):
    session_type: str = "behavioral"
    num_questions: int = 8


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    question_text: str = Field(default="", max_length=2_000)
    answer_text: str = Field(min_length=1, max_length=20_000)
    answer_order: int = 0
