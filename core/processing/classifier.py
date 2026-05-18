import logging
from llm.router import llm_router, LLMError
from llm.prompts import CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

PROFESSIONAL_KEYWORDS = [
    "api", "database", "bug", "error", "deploy", "code", "server",
    "architecture", "client", "sprint", "deadline", "code review",
    "production", "migration", "performance", "system", "endpoint",
    "backend", "frontend", "pipeline", "infrastructure", "kubernetes",
    "docker", "redis", "postgresql", "fastapi", "django", "react",
    "debugging", "refactor", "pull request", "merge", "release",
    "stakeholder", "product manager", "team lead", "manager",
    "requirement", "specification", "roadmap", "feature", "codebase",
    "repository", "git", "ci/cd", "devops", "microservice", "latency",
    "throughput", "scalability", "load balancer", "cache", "queue",
]

PERSONAL_KEYWORDS = [
    "recipe", "movie", "fitness", "workout", "diet", "weight",
    "relationship", "girlfriend", "boyfriend", "wife", "husband",
    "family", "mom", "dad", "sister", "brother", "travel", "vacation",
    "birthday", "medical", "doctor", "health symptom", "religion",
    "politics", "game", "sports score", "music playlist", "netflix",
    "amazon prime", "book recommendation", "restaurant", "food",
]

AMBIGUOUS_SIGNALS = [
    "i tend to", "i've realized", "i struggle with",
    "my manager", "at work", "in my career", "i feel",
    "i'm thinking about", "communication", "leadership style",
    "my team", "our team", "in my experience", "i've learned",
]

VALID_CATEGORIES = {"PROFESSIONAL", "BEHAVIORAL_PRO", "PERSONAL", "MIXED"}


async def classify(segment: dict) -> str:
    text = " ".join(segment.get("messages", [])).lower()

    has_professional = any(kw in text for kw in PROFESSIONAL_KEYWORDS)
    has_personal = any(kw in text for kw in PERSONAL_KEYWORDS)

    if has_professional and not has_personal:
        return "PROFESSIONAL"
    if has_personal and not has_professional:
        return "PERSONAL"

    # Ambiguous — check signals then call LLM
    has_ambiguous = any(sig in text for sig in AMBIGUOUS_SIGNALS)

    if has_professional and has_personal:
        llm_hint = "MIXED"
    elif has_ambiguous or not has_professional:
        llm_hint = None  # needs LLM
    else:
        return "PROFESSIONAL"

    if llm_hint == "MIXED":
        # Still confirm with LLM if both are present
        pass

    user_messages_text = "\n---\n".join(segment.get("messages", []))
    prompt = CLASSIFICATION_PROMPT.format(user_messages=user_messages_text[:2000])

    try:
        result = await llm_router.call("classify", prompt, max_tokens=60)
        parsed = llm_router.parse_json_response(result)
        category = parsed.get("category", "").upper()
        if category in VALID_CATEGORIES:
            return category
        return "PROFESSIONAL"  # safe default
    except (LLMError, ValueError) as e:
        logger.warning(f"Classifier LLM failed: {e}. Defaulting to PROFESSIONAL.")
        return "PROFESSIONAL"
