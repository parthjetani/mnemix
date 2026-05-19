"""Single-source helper for resolving the active user's profile row.

For the v0.1 demo there is only one user, so every query falls back to the
hardcoded `id=1` row. This module is the only place that hardcode lives — when
multi-user support lands, every call site already takes a `UserContext` and
the helper switches to look up by `user_id` instead.
"""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserProfileORM


# Single-user demo: the one profile row has id=1.
_DEMO_PROFILE_ID = 1


@dataclass(frozen=True)
class UserContext:
    """Carries the active user identity through the call chain."""
    user_id: str = "default"


def default_user_context() -> UserContext:
    return UserContext(user_id="default")


async def get_user_profile_orm(
    ctx: UserContext,
    db: AsyncSession,
) -> UserProfileORM | None:
    """Fetch the profile row for the given user. Returns None if missing."""
    # TODO multi-user: filter by ctx.user_id once user_id column is populated.
    _ = ctx  # currently unused; retained so call sites are already shaped right
    result = await db.execute(
        select(UserProfileORM).where(UserProfileORM.id == _DEMO_PROFILE_ID)
    )
    return result.scalar_one_or_none()


async def get_or_create_user_profile_orm(
    ctx: UserContext,
    db: AsyncSession,
) -> UserProfileORM:
    """Same as get_user_profile_orm but inserts an empty default row if missing."""
    row = await get_user_profile_orm(ctx, db)
    if row is None:
        row = UserProfileORM(id=_DEMO_PROFILE_ID)
        db.add(row)
    return row
