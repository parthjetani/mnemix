from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict


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


# ─── API Request/Response schemas ─────────────────────────────────────────────

class IngestResponse(BaseModel):
    job_id: str
    status: str
    message: str


class MemoryAddRequest(BaseModel):
    content: str
    category: str
    themes: list[str] = []


class InterviewStartRequest(BaseModel):
    session_type: str = "behavioral"
    num_questions: int = 8


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    question_text: str = ""
    answer_text: str
    answer_order: int = 0
