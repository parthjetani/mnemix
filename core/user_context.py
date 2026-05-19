"""Resolves the active user's identity and profile row.

get_user_context is a FastAPI dependency that extracts the Supabase user ID
from the validated JWT and returns a UserContext. All endpoints and core
functions accept UserContext so user_id flows through naturally.
"""
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from database import UserProfileORM


@dataclass(frozen=True)
class UserContext:
    """Carries the active user's Supabase UUID through the call chain."""
    user_id: str


async def get_user_context(user: dict = Depends(get_current_user)) -> UserContext:
    """FastAPI dependency — validates JWT then returns a UserContext."""
    return UserContext(user_id=user["id"])


async def get_user_profile_orm(
    ctx: UserContext,
    db: AsyncSession,
) -> UserProfileORM | None:
    """Fetch the profile row for this user. Returns None if not yet created."""
    result = await db.execute(
        select(UserProfileORM).where(UserProfileORM.user_id == ctx.user_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_user_profile_orm(
    ctx: UserContext,
    db: AsyncSession,
) -> UserProfileORM:
    """Return the profile row, creating a default one on first sign-in."""
    row = await get_user_profile_orm(ctx, db)
    if row is None:
        row = UserProfileORM(user_id=ctx.user_id)
        db.add(row)
        await db.flush()
    return row
