import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from core.rate_limit import limiter
from core.user_context import UserContext, get_user_context, get_or_create_user_profile_orm, get_user_profile_orm
from core.memory.profile_synthesizer import synthesize_profile, orm_to_profile_schema
from models.schemas import UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserProfile)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    ctx: UserContext = Depends(get_user_context),
):
    row = await get_user_profile_orm(ctx, db)
    if not row:
        return UserProfile(
            field="software_engineering", seniority="mid",
            primary_stack=[], target_roles=[], strength_areas=[], gap_areas=[],
        )
    return orm_to_profile_schema(row)


@router.put("", response_model=UserProfile)
async def update_profile(
    data: dict,
    db: AsyncSession = Depends(get_db),
    ctx: UserContext = Depends(get_user_context),
):
    row = await get_or_create_user_profile_orm(ctx, db)

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

    row.last_updated = datetime.now(timezone.utc).isoformat()

    await db.commit()
    await db.refresh(row)

    return orm_to_profile_schema(row)


@router.post("/synthesize", response_model=UserProfile)
@limiter.limit("10/hour")
async def synthesize_profile_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    ctx: UserContext = Depends(get_user_context),
):
    profile = await synthesize_profile(ctx, db)
    await db.commit()
    return profile
