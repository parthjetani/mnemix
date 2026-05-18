import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import InterviewSessionORM, UserProfileORM
from llm.router import llm_router, LLMError
from llm.prompts import FEEDBACK_PROMPT
from models.schemas import EvaluationResult, FeedbackReport

logger = logging.getLogger(__name__)


async def generate_feedback(
    session_id: str,
    evaluations: list[EvaluationResult],
    db: AsyncSession,
) -> FeedbackReport:
    if not evaluations:
        return FeedbackReport(
            session_id=session_id,
            overall_score=0.0,
            report_text="No answers were evaluated for this session.",
            evaluations=[],
        )

    overall_score = round(sum(e.total_score for e in evaluations) / len(evaluations), 1)

    # Build profile summary
    profile_result = await db.execute(select(UserProfileORM).where(UserProfileORM.id == 1))
    profile = profile_result.scalar_one_or_none()
    profile_summary = "Software engineer, mid-level"
    if profile:
        profile_summary = (
            f"Field: {profile.field or 'software engineering'}, "
            f"Seniority: {profile.seniority or 'mid'}"
        )
        if profile.career_narrative:
            profile_summary += f"\n{profile.career_narrative}"

    # Serialize evaluations for the prompt
    evals_text = json.dumps([
        {
            "question": e.question_text,
            "answer_summary": e.answer_text[:300] + "..." if len(e.answer_text) > 300 else e.answer_text,
            "memory_match": e.memory_match,
            "specificity": e.specificity,
            "outcome_stated": e.outcome_stated,
            "outcome_quantified": e.outcome_quantified,
            "coherence": e.coherence,
            "score": e.total_score,
            "specific_feedback": e.specific_feedback,
            "memory_missed": e.memory_opportunity_missed,
        }
        for e in evaluations
    ], indent=2)

    prompt = FEEDBACK_PROMPT.format(
        field=profile.field if profile else "software engineering",
        profile_summary=profile_summary,
        all_evaluations=evals_text,
        score=int(overall_score),
    )

    try:
        report_text = await llm_router.call("feedback", prompt, max_tokens=1500)
    except LLMError as e:
        logger.error(f"Feedback generation failed: {e}")
        report_text = _fallback_report(evaluations, overall_score)

    # Update session record
    session_result = await db.execute(
        select(InterviewSessionORM).where(InterviewSessionORM.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if session:
        session.overall_score = overall_score
        session.status = "complete"
        session.feedback_report = report_text
        await db.flush()

    return FeedbackReport(
        session_id=session_id,
        overall_score=overall_score,
        report_text=report_text,
        evaluations=evaluations,
    )


def _fallback_report(evaluations: list[EvaluationResult], overall_score: float) -> str:
    lines = [
        f"OVERALL SCORE: {overall_score}/100\n",
        "─" * 50,
    ]
    for i, e in enumerate(evaluations, 1):
        lines.append(f"\nQ{i}: {e.question_text}")
        lines.append(f"Score: {e.total_score}/100")
        lines.append(f"Feedback: {e.specific_feedback}")
    return "\n".join(lines)
