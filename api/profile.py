import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, UserProfileORM
from core.auth import get_current_user
from models.schemas import UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserProfile)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(select(UserProfileORM).where(UserProfileORM.id == 1))
    row = result.scalar_one_or_none()
    if not row:
        return UserProfile(
            id=1, field="software_engineering", seniority="mid",
            primary_stack=[], target_roles=[], strength_areas=[], gap_areas=[],
        )
    return UserProfile(
        id=row.id,
        field=row.field or "software_engineering",
        seniority=row.seniority or "mid",
        primary_stack=json.loads(row.primary_stack or "[]"),
        target_roles=json.loads(row.target_roles or "[]"),
        strength_areas=json.loads(row.strength_areas or "[]"),
        gap_areas=json.loads(row.gap_areas or "[]"),
        career_narrative=row.career_narrative,
        last_updated=row.last_updated,
    )


@router.put("", response_model=UserProfile)
async def update_profile(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(select(UserProfileORM).where(UserProfileORM.id == 1))
    row = result.scalar_one_or_none()

    if not row:
        row = UserProfileORM(id=1)
        db.add(row)

    if "field" in data:
        row.field = data["field"]
    if "seniority" in data:
        row.seniority = data["seniority"]
    if "primary_stack" in data:
        row.primary_stack = json.dumps(data["primary_stack"])
    if "target_roles" in data:
        row.target_roles = json.dumps(data["target_roles"])
    if "career_narrative" in data:
        row.career_narrative = data["career_narrative"]

    await db.commit()
    await db.refresh(row)

    return UserProfile(
        id=row.id,
        field=row.field or "software_engineering",
        seniority=row.seniority or "mid",
        primary_stack=json.loads(row.primary_stack or "[]"),
        target_roles=json.loads(row.target_roles or "[]"),
        strength_areas=json.loads(row.strength_areas or "[]"),
        gap_areas=json.loads(row.gap_areas or "[]"),
        career_narrative=row.career_narrative,
        last_updated=row.last_updated,
    )
