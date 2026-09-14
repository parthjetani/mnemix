import json
import logging
import uuid

from database import UserProfileORM
from llm.router import llm_router
from llm.prompts import Q_BEHAVIORAL_PROMPT, Q_TECHNICAL_PROMPT
from models.schemas import Question

logger = logging.getLogger(__name__)


def _profile_summary(profile: UserProfileORM | None) -> str:
    if not profile:
        return "Software engineer, mid-level"
    summary = f"Field: {profile.field or 'software engineering'}, Seniority: {profile.seniority or 'mid'}"
    if profile.career_narrative:
        summary += f"\n{profile.career_narrative}"
    return summary


async def generate_behavioral_question(category: str, profile: UserProfileORM | None) -> Question | None:
    prompt = Q_BEHAVIORAL_PROMPT.format(category=category, profile_summary=_profile_summary(profile))
    try:
        raw = await llm_router.call("q_behavioral", prompt, max_tokens=200)
    except Exception as e:
        logger.warning(f"q_behavioral generation failed for category '{category}': {e}")
        return None
    text = llm_router.strip_plain_text(raw)
    if not text:
        return None
    return Question(id=f"llm-{uuid.uuid4()}", text=text, category=category, source="llm_generated")


async def generate_technical_question(category: str, profile: UserProfileORM | None) -> Question | None:
    stack_list = []
    if profile and profile.primary_stack:
        try:
            stack_list = json.loads(profile.primary_stack)
        except (TypeError, ValueError):
            stack_list = []
    stack = ", ".join(stack_list) if stack_list else "general software engineering"
    seniority = profile.seniority if profile and profile.seniority else "mid"
    prompt = Q_TECHNICAL_PROMPT.format(category=category, stack=stack, seniority=seniority)
    try:
        # Generous budget: qwen3-32b is a reasoning model and spends most of it on the hidden <think> block.
        raw = await llm_router.call("q_technical", prompt, max_tokens=900)
    except Exception as e:
        logger.warning(f"q_technical generation failed for category '{category}': {e}")
        return None
    text = llm_router.strip_plain_text(raw)
    if not text:
        return None
    return Question(id=f"llm-{uuid.uuid4()}", text=text, category=category, source="llm_generated")
