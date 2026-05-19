import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from database import InterviewSessionORM, get_db
from core.auth import get_current_user
from core.interview.question_bank import select_questions
from core.interview.session import (
    create_session,
    add_answer,
    get_next_question,
    complete_session,
    get_session_answers,
)
from core.interview.evaluator import evaluate_session
from core.interview.feedback import generate_feedback
from models.schemas import InterviewStartRequest, AnswerRequest, FeedbackReport

router = APIRouter(prefix="/interview", tags=["interview"])


async def _run_evaluation(session_id: str) -> None:
    from database import async_session_factory
    # Small delay so the submit_answer transaction fully commits before we start writing
    await asyncio.sleep(1.5)
    for attempt in range(3):
        async with async_session_factory() as db:
            try:
                evaluations = await evaluate_session(session_id, db)
                await generate_feedback(session_id, evaluations, db)
                await db.commit()
                return
            except Exception as exc:
                await db.rollback()
                if attempt < 2 and "locked" in str(exc).lower():
                    logger.warning(f"Evaluation attempt {attempt+1} hit DB lock, retrying in 3s…")
                    await asyncio.sleep(3)
                else:
                    logger.error(f"Evaluation background task failed for {session_id}: {exc}", exc_info=True)
                    return


@router.post("/start")
async def start_interview(
    request: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    questions = await select_questions(request.session_type, db, count=8)
    if not questions:
        raise HTTPException(status_code=500, detail="No questions available — seed the question bank first")

    session = await create_session(request.session_type, questions, db)

    next_q = await get_next_question(session.id, db)

    return {
        "session_id": session.id,
        "session_type": request.session_type,
        "total_questions": len(questions),
        "questions": [q.model_dump() for q in questions],
        "current_question": next_q,
    }


@router.post("/answer")
async def submit_answer(
    request: AnswerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    session_result = await db.execute(
        select(InterviewSessionORM).where(InterviewSessionORM.id == request.session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in ("in_progress", "evaluating"):
        raise HTTPException(status_code=400, detail=f"Session is {session.status}, cannot accept answers")

    await add_answer(
        session_id=request.session_id,
        question_id=request.question_id,
        question_text=request.question_text,
        answer_text=request.answer_text,
        answer_order=request.answer_order,
        db=db,
    )

    next_q = await get_next_question(request.session_id, db)

    if next_q is None:
        await complete_session(request.session_id, db)
        background_tasks.add_task(_run_evaluation, request.session_id)
        return {
            "session_complete": True,
            "session_id": request.session_id,
            "next_question": None,
            "message": "All answers received. Evaluation in progress.",
        }

    return {
        "session_complete": False,
        "session_id": request.session_id,
        "next_question": next_q,
    }


@router.get("/evaluate/{session_id}")
async def get_evaluation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    session_result = await db.execute(
        select(InterviewSessionORM).where(InterviewSessionORM.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "evaluating":
        return {"status": "evaluating", "message": "Evaluation in progress, try again in a few seconds"}

    if session.status != "complete":
        return {"status": session.status, "message": f"Session is {session.status}"}

    answers = await get_session_answers(session_id, db)
    import json
    from models.schemas import EvaluationResult

    evaluations = []
    for a in answers:
        evaluations.append(EvaluationResult(
            question_id=a.question_id or "",
            question_text=a.question_text or "",
            answer_text=a.answer_text or "",
            memory_match=int(a.memory_match_score or 0),
            specificity=int(a.specificity_score or 0),
            outcome_stated=a.outcome_stated or False,
            outcome_quantified=a.outcome_quantified or False,
            memory_opportunity_missed=a.memory_opportunity,
            coherence=int(getattr(a, "coherence_score", 0) or 0),
            specific_feedback=a.feedback_text or "",
            total_score=a.total_score or 0.0,
        ))

    return FeedbackReport(
        session_id=session_id,
        overall_score=session.overall_score or 0.0,
        report_text=session.feedback_report or "",
        evaluations=evaluations,
    )


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(InterviewSessionORM).order_by(InterviewSessionORM.started_at.desc()).limit(20)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "session_type": s.session_type,
            "status": s.status,
            "started_at": s.started_at,
            "completed_at": s.completed_at,
            "overall_score": s.overall_score,
        }
        for s in sessions
    ]
