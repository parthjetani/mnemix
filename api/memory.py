import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import MemoryORM, get_db
from core.auth import get_current_user
from core.user_context import default_user_context, get_user_profile_orm
from llm.embeddings import embed
from core.memory.store import save_memory, count_memories_by_category
from core.memory.retriever_pgvector import memory_retriever
from core.memory.gap_detector import detect_gaps
from models.schemas import Memory, MemoryAddRequest

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/profile")
async def get_memory_profile(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    category_counts = await count_memories_by_category(db)

    result = await db.execute(select(MemoryORM).order_by(MemoryORM.access_count.desc()).limit(5))
    top_memories_orm = result.scalars().all()
    top_memories = [
        {
            "id": m.id,
            "content": m.content,
            "category": m.category,
            "confidence": m.confidence,
            "access_count": m.access_count,
        }
        for m in top_memories_orm
    ]

    profile = await get_user_profile_orm(default_user_context(), db)
    profile_data = None
    if profile:
        profile_data = {
            "field": profile.field,
            "seniority": profile.seniority,
            "career_narrative": profile.career_narrative,
            "primary_stack": profile.primary_stack,
        }

    return {
        "total_memories": sum(category_counts.values()),
        "by_category": category_counts,
        "top_memories": top_memories,
        "profile": profile_data,
    }


@router.get("/gaps")
async def get_memory_gaps(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    gaps = await detect_gaps(db)
    return {"gaps": gaps, "total_gaps": len(gaps)}


@router.post("/add", response_model=Memory)
async def add_memory(
    request: MemoryAddRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    embedding = embed(request.content)
    memory_id = await save_memory(request, embedding, db)
    await memory_retriever.add_to_index(memory_id, embedding)

    result = await db.execute(select(MemoryORM).where(MemoryORM.id == memory_id))
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=500, detail="Memory save failed")

    return Memory(
        id=orm.id,
        content=orm.content,
        category=orm.category,
        themes=json.loads(orm.themes) if orm.themes else [],
        interview_qs=json.loads(orm.interview_qs) if orm.interview_qs else [],
        confidence=orm.confidence or 0.0,
        source=orm.source or "manual",
        date_context=orm.date_context,
        has_outcome=orm.has_outcome or False,
        outcome_quantified=orm.outcome_quantified or False,
        created_at=orm.created_at or "",
        access_count=orm.access_count or 0,
        last_accessed=orm.last_accessed,
    )


@router.get("/search")
async def search_memories(
    q: str,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results = await memory_retriever.search(q, db, top_k=min(top_k, 20))
    return [
        {"memory": mem.model_dump(exclude={"embedding"}), "similarity": round(score, 4)}
        for mem, score in results
    ]


@router.get("/list")
async def list_memories(
    category: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    stmt = select(MemoryORM).order_by(MemoryORM.created_at.desc()).limit(min(limit, 200))
    if category:
        stmt = (
            select(MemoryORM)
            .where(MemoryORM.category == category)
            .order_by(MemoryORM.created_at.desc())
            .limit(min(limit, 200))
        )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": m.id,
            "content": m.content,
            "category": m.category,
            "themes": json.loads(m.themes) if m.themes else [],
            "confidence": m.confidence or 0.0,
            "source": m.source or "manual",
            "has_outcome": m.has_outcome or False,
            "outcome_quantified": m.outcome_quantified or False,
            "created_at": m.created_at or "",
            "access_count": m.access_count or 0,
        }
        for m in rows
    ]
