import json
import random
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import QuestionORM
from models.schemas import Question
from core.memory.gap_detector import detect_gaps

_SEED_PATH = Path(__file__).parent.parent.parent / "data" / "questions_seed.json"

BEHAVIORAL_CATEGORIES = [
    "leadership", "conflict_resolution", "failure_learning", "collaboration",
    "pressure_handling", "initiative", "communication", "ambiguity_handling",
]
TECHNICAL_CATEGORIES = [
    "system_design", "debugging", "tech_decisions",
    "performance_optimization", "architecture",
]
IDENTITY_CATEGORIES = ["career_goal", "value", "strength", "working_style", "self_awareness"]


async def load_questions(db: AsyncSession) -> int:
    data = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    count = 0
    for q in data:
        existing = await db.execute(
            select(QuestionORM).where(QuestionORM.id == q["id"])
        )
        if existing.scalar_one_or_none() is None:
            db.add(QuestionORM(
                id=q["id"],
                text=q["text"],
                category=q["category"],
                field=q.get("field"),
                seniority=q.get("seniority"),
                source=q.get("source", "seeded"),
            ))
            count += 1
    await db.flush()
    return count


async def _random_question_by_category(
    category: str,
    db: AsyncSession,
    exclude_ids: set[str] | None = None,
) -> Question | None:
    result = await db.execute(
        select(QuestionORM)
        .where(QuestionORM.category == category)
        .order_by(func.random())
        .limit(10)
    )
    rows = result.scalars().all()
    if not rows:
        return None
    exclude = exclude_ids or set()
    candidates = [r for r in rows if r.id not in exclude] or list(rows)
    row = candidates[0]
    return _orm_to_schema(row)


async def select_questions(
    session_type: str,
    db: AsyncSession,
    count: int = 8,
) -> list[Question]:
    selected: list[Question] = []
    used_ids: set[str] = set()

    # 1. Universal opener — always first
    opener = await _random_question_by_category("career_goal", db, used_ids)
    if opener:
        selected.append(opener)
        used_ids.add(opener.id)

    # 2. Gap questions — highest priority first (up to 2)
    gaps = await detect_gaps(db)
    gap_categories = [g["category"] for g in gaps if g["priority"] == "high"][:3]
    for cat in gap_categories:
        if len(selected) >= count - 2:
            break
        q = await _random_question_by_category(cat, db, used_ids)
        if q:
            selected.append(q)
            used_ids.add(q.id)

    # 3. Session-type specific questions
    if session_type == "behavioral":
        pool = BEHAVIORAL_CATEGORIES
    elif session_type == "technical":
        pool = TECHNICAL_CATEGORIES
    else:  # mixed
        pool = BEHAVIORAL_CATEGORIES + TECHNICAL_CATEGORIES

    random.shuffle(pool)
    for cat in pool:
        if len(selected) >= count - 1:
            break
        q = await _random_question_by_category(cat, db, used_ids)
        if q:
            selected.append(q)
            used_ids.add(q.id)

    # 4. Random wildcard — keep it unpredictable
    all_cats = BEHAVIORAL_CATEGORIES + TECHNICAL_CATEGORIES + IDENTITY_CATEGORIES
    for cat in random.sample(all_cats, len(all_cats)):
        if len(selected) >= count:
            break
        q = await _random_question_by_category(cat, db, used_ids)
        if q:
            selected.append(q)
            used_ids.add(q.id)

    # Shuffle everything except opener, trim to count
    middle = selected[1:]
    random.shuffle(middle)
    final = ([selected[0]] + middle)[:count] if selected else middle[:count]
    return final


def _orm_to_schema(row: QuestionORM) -> Question:
    return Question(
        id=row.id,
        text=row.text,
        category=row.category or "",
        field=row.field,
        seniority=row.seniority,
        source=row.source or "seeded",
        effectiveness_score=row.effectiveness_score or 0.5,
        use_count=row.use_count or 0,
    )
