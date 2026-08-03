import json
import uuid
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import MemoryORM
from models.schemas import Memory as MemorySchema, MemoryCreate


async def save_memory(
    memory: MemoryCreate,
    embedding: np.ndarray,
    db: AsyncSession,
    user_id: str = "default",
) -> str:
    memory_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    emb_f32 = embedding.astype(np.float32)

    orm_obj = MemoryORM(
        id=memory_id,
        user_id=user_id,
        content=memory.content,
        category=memory.category,
        themes=json.dumps(memory.themes),
        interview_qs=json.dumps(memory.interview_qs),
        confidence=memory.confidence,
        source=memory.source,
        date_context=memory.date_context,
        has_outcome=memory.has_outcome,
        outcome_quantified=memory.outcome_quantified,
        embedding=emb_f32.tobytes(),
        embedding_vec=emb_f32.tolist(),
        created_at=now,
        access_count=0,
    )
    db.add(orm_obj)
    await db.flush()
    return memory_id


async def get_all_memories(
    db: AsyncSession,
    user_id: str | None = None,
) -> list[tuple[MemorySchema, np.ndarray]]:
    stmt = select(MemoryORM)
    if user_id is not None:
        stmt = stmt.where(MemoryORM.user_id == user_id)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    out = []
    for row in rows:
        schema = _orm_to_schema(row)
        embedding = np.frombuffer(row.embedding, dtype=np.float32).copy()
        out.append((schema, embedding))
    return out


async def count_memories_by_category(
    db: AsyncSession,
    user_id: str | None = None,
) -> dict[str, int]:
    stmt = select(MemoryORM.category, func.count(MemoryORM.id)).group_by(MemoryORM.category)
    if user_id is not None:
        stmt = stmt.where(MemoryORM.user_id == user_id)
    result = await db.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


async def get_memories_by_ids(
    memory_ids: list[str],
    db: AsyncSession,
) -> dict[str, MemorySchema]:
    """Batch fetch — one query instead of N. Returns id -> schema map."""
    if not memory_ids:
        return {}
    result = await db.execute(
        select(MemoryORM).where(MemoryORM.id.in_(memory_ids))
    )
    return {row.id: _orm_to_schema(row) for row in result.scalars().all()}


async def increment_access_count(memory_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(MemoryORM).where(MemoryORM.id == memory_id)
    )
    row = result.scalar_one_or_none()
    if row:
        row.access_count = (row.access_count or 0) + 1
        row.last_accessed = datetime.now(timezone.utc).isoformat()
        await db.flush()


def _orm_to_schema(row: MemoryORM) -> MemorySchema:
    return MemorySchema(
        id=row.id,
        content=row.content,
        category=row.category,
        themes=_safe_json_list(row.themes),
        interview_qs=_safe_json_list(row.interview_qs),
        confidence=row.confidence or 0.0,
        source=row.source or "",
        date_context=row.date_context,
        has_outcome=bool(row.has_outcome),
        outcome_quantified=bool(row.outcome_quantified),
        created_at=row.created_at or "",
        access_count=row.access_count or 0,
        last_accessed=row.last_accessed,
    )


def _safe_json_list(value) -> list:
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except Exception:
        return []
