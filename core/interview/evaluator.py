import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from database import SessionAnswerORM
from llm.router import llm_router, LLMError
from llm.prompts import EVALUATION_PROMPT
from core.memory.retriever_pgvector import memory_retriever
from core.memory.store import increment_access_count
from core.user_context import UserContext, get_user_profile_orm
from models.schemas import EvaluationResult

logger = logging.getLogger(__name__)


async def _evaluate_single_answer(
    answer_orm: SessionAnswerORM,
    field: str,
    seniority: str,
    db: AsyncSession,
    user_id: str | None = None,
) -> EvaluationResult:
    answer_text = answer_orm.answer_text or ""
    question_text = answer_orm.question_text or ""

    # Retrieve top memories relevant to this answer (scoped to this user)
    top_memories = await memory_retriever.search(answer_text, db, top_k=5, user_id=user_id)

    top_memories_text = json.dumps([
        {"id": m.id, "content": m.content, "category": m.category}
        for m, _ in top_memories
    ], indent=2)

    # Determine which eval task to use (system design gets deeper reasoning)
    task = "eval_sysdesign" if answer_orm.question_id and "sysdes" in answer_orm.question_id else "eval"

    prompt = EVALUATION_PROMPT.format(
        field=field,
        seniority=seniority,
        question=question_text,
        answer=answer_text,
        top_memories=top_memories_text,
        memory_summary=f"Field: {field}, Seniority: {seniority}",
    )

    try:
        result = await llm_router.call(task, prompt, max_tokens=400)
        parsed = llm_router.parse_json_response(result)
    except (LLMError, ValueError) as e:
        logger.warning(f"Evaluation failed for answer {answer_orm.id}: {e}")
        parsed = {
            "memory_match": 0, "specificity": 0,
            "outcome_stated": False, "outcome_quantified": False,
            "memory_opportunity_missed": None, "coherence": 1,
            "specific_feedback": "Evaluation unavailable for this answer.",
        }

    memory_match = int(parsed.get("memory_match", 0))
    specificity = int(parsed.get("specificity", 0))
    outcome_stated = bool(parsed.get("outcome_stated", False))
    outcome_quantified = bool(parsed.get("outcome_quantified", False))
    coherence = int(parsed.get("coherence", 0))
    missed = parsed.get("memory_opportunity_missed")

    # Normalize to 0-100: max possible = 3+3+2+1+2 = 11
    raw_score = memory_match + specificity + (2 if outcome_stated else 0) + (1 if outcome_quantified else 0) + coherence
    total_score = round((raw_score / 11) * 100, 1)

    # Update DB row with scores
    answer_orm.memory_match_score = float(memory_match)
    answer_orm.specificity_score = float(specificity)
    answer_orm.outcome_stated = outcome_stated
    answer_orm.outcome_quantified = outcome_quantified
    answer_orm.coherence_score = float(coherence)
    answer_orm.memory_opportunity = missed
    answer_orm.total_score = total_score
    answer_orm.feedback_text = parsed.get("specific_feedback", "")

    # Increment access count on retrieved memories
    for mem, _ in top_memories:
        await increment_access_count(mem.id, db)

    return EvaluationResult(
        question_id=answer_orm.question_id or "",
        question_text=question_text,
        answer_text=answer_text,
        memory_match=memory_match,
        specificity=specificity,
        outcome_stated=outcome_stated,
        outcome_quantified=outcome_quantified,
        memory_opportunity_missed=missed,
        coherence=coherence,
        specific_feedback=parsed.get("specific_feedback", ""),
        total_score=total_score,
    )


async def evaluate_session(
    session_id: str,
    db: AsyncSession,
    user_id: str | None = None,
    field: str = "software_engineering",
    seniority: str = "mid",
) -> list[EvaluationResult]:
    from core.interview.session import get_session_answers

    # Try to get field/seniority from user profile
    if user_id is not None:
        profile = await get_user_profile_orm(UserContext(user_id=user_id), db)
        if profile:
            field = profile.field or field
            seniority = profile.seniority or seniority

    answers = await get_session_answers(session_id, db)
    if not answers:
        return []

    # Evaluate all answers in parallel
    tasks = [_evaluate_single_answer(a, field, seniority, db, user_id=user_id) for a in answers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    evaluations: list[EvaluationResult] = []
    for res in results:
        if isinstance(res, EvaluationResult):
            evaluations.append(res)
        else:
            logger.error(f"Evaluation task failed: {res}")

    await db.flush()
    return evaluations
