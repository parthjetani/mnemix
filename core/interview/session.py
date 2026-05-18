import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import InterviewSessionORM, SessionAnswerORM
from models.schemas import InterviewSession, SessionAnswer, Question


async def create_session(
    session_type: str,
    questions: list[Question],
    db: AsyncSession,
) -> InterviewSession:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    questions_list = [{"id": q.id, "text": q.text, "category": q.category} for q in questions]

    orm = InterviewSessionORM(
        id=session_id,
        started_at=now,
        session_type=session_type,
        status="in_progress",
        questions_list=json.dumps(questions_list),
    )
    db.add(orm)
    await db.flush()

    return InterviewSession(
        id=session_id,
        started_at=now,
        session_type=session_type,
        status="in_progress",
        questions_list=json.dumps(questions_list),
    )


async def get_next_question(
    session_id: str,
    db: AsyncSession,
) -> dict | None:
    """Return the next unanswered question dict, or None if session is complete."""
    result = await db.execute(
        select(InterviewSessionORM).where(InterviewSessionORM.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session or not session.questions_list:
        return None

    questions = json.loads(session.questions_list)

    answered = await db.execute(
        select(SessionAnswerORM.question_id).where(SessionAnswerORM.session_id == session_id)
    )
    answered_ids = {row[0] for row in answered.all()}

    for i, q in enumerate(questions):
        if q["id"] not in answered_ids:
            return {"index": i, "total": len(questions), **q}

    return None


async def add_answer(
    session_id: str,
    question_id: str,
    question_text: str,
    answer_text: str,
    answer_order: int,
    db: AsyncSession,
) -> SessionAnswer:
    now = datetime.now(timezone.utc).isoformat()
    answer_id = str(uuid.uuid4())

    orm = SessionAnswerORM(
        id=answer_id,
        session_id=session_id,
        question_id=question_id,
        question_text=question_text,
        answer_text=answer_text,
        answer_order=answer_order,
        created_at=now,
    )
    db.add(orm)
    await db.flush()

    return SessionAnswer(
        id=answer_id,
        session_id=session_id,
        question_id=question_id,
        question_text=question_text,
        answer_text=answer_text,
        answer_order=answer_order,
        created_at=now,
    )


async def complete_session(session_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(InterviewSessionORM).where(InterviewSessionORM.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        session.status = "evaluating"
        session.completed_at = datetime.now(timezone.utc).isoformat()
        await db.flush()


async def get_session_answers(session_id: str, db: AsyncSession) -> list[SessionAnswerORM]:
    result = await db.execute(
        select(SessionAnswerORM)
        .where(SessionAnswerORM.session_id == session_id)
        .order_by(SessionAnswerORM.answer_order)
    )
    return list(result.scalars().all())
