import json
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database import UserProfileORM
from core.user_context import UserContext, get_or_create_user_profile_orm
from core.memory.store import count_memories_by_category, get_memories_by_category
from llm.router import llm_router, LLMError
from llm.prompts import PROFILE_PROMPT
from models.schemas import UserProfile

logger = logging.getLogger(__name__)

SAMPLE_CATEGORIES = 6
SAMPLES_PER_CATEGORY = 2


def orm_to_profile_schema(row: UserProfileORM) -> UserProfile:
    return UserProfile(
        field=row.field or "software_engineering",
        seniority=row.seniority or "mid",
        primary_stack=json.loads(row.primary_stack or "[]"),
        target_roles=json.loads(row.target_roles or "[]"),
        communication_style=row.communication_style,
        strength_areas=json.loads(row.strength_areas or "[]"),
        gap_areas=json.loads(row.gap_areas or "[]"),
        career_narrative=row.career_narrative,
        last_updated=row.last_updated,
    )


async def synthesize_profile(ctx: UserContext, db: AsyncSession) -> UserProfile:
    row = await get_or_create_user_profile_orm(ctx, db)
    counts = await count_memories_by_category(db, user_id=ctx.user_id)

    if not counts:
        return orm_to_profile_schema(row)

    memory_summary = "\n".join(
        f"- {cat}: {n}" for cat, n in sorted(counts.items(), key=lambda kv: -kv[1])
    )
    top_categories = sorted(counts, key=lambda c: -counts[c])[:SAMPLE_CATEGORIES]
    sample_lines = []
    for cat in top_categories:
        mems = await get_memories_by_category(cat, db, user_id=ctx.user_id)
        sample_lines += [f"[{cat}] {m.content}" for m in mems[:SAMPLES_PER_CATEGORY]]
    sample_memories = "\n".join(sample_lines) or "(no sample memories available)"

    prompt = PROFILE_PROMPT.format(
        field=row.field or "software_engineering",
        memory_summary=memory_summary,
        sample_memories=sample_memories,
    )

    try:
        result = await llm_router.call("profile", prompt, max_tokens=600)
        parsed = llm_router.parse_json_response(result)
        row.communication_style = parsed.get("communication_style") or row.communication_style
        row.strength_areas = json.dumps(parsed.get("strength_areas") or [])
        row.gap_areas = json.dumps(parsed.get("gap_areas") or [])
        row.career_narrative = parsed.get("career_narrative") or row.career_narrative
    except (LLMError, ValueError) as e:
        logger.warning(f"Profile synthesis LLM failed for user {ctx.user_id}: {e}")
        # Heuristic fallback, matching the prompt's own documented thresholds.
        row.strength_areas = json.dumps([c for c, n in counts.items() if n >= 3])
        row.gap_areas = json.dumps([c for c, n in counts.items() if n <= 1])

    row.last_updated = datetime.now(timezone.utc).isoformat()
    await db.flush()
    return orm_to_profile_schema(row)
