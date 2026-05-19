import json
import logging
from openai import AsyncOpenAI, OpenAIError

from config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


groq_client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url=settings.GROQ_BASE_URL,
)

openrouter_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

# All tasks route to Groq. OpenRouter is the fallback.
TASK_ROUTES: dict[str, tuple[str, AsyncOpenAI]] = {
    "classify":       (settings.MODEL_CLASSIFY,       groq_client),
    "extract":        (settings.MODEL_EXTRACT,         groq_client),
    "profile":        (settings.MODEL_PROFILE,         groq_client),
    "q_behavioral":   (settings.MODEL_Q_BEHAVIORAL,    groq_client),
    "q_technical":    (settings.MODEL_Q_TECHNICAL,     groq_client),
    "eval":           (settings.MODEL_EVAL,            groq_client),
    "eval_sysdesign": (settings.MODEL_EVAL_SYSDESIGN,  groq_client),
    "feedback":       (settings.MODEL_FEEDBACK,        groq_client),
    "gap_analysis":   (settings.MODEL_GAP_ANALYSIS,    groq_client),
}

# OpenRouter fallback: reasoning tasks get the R1 free model, others get Llama
OPENROUTER_FALLBACKS: dict[str, str] = {
    "classify":       settings.MODEL_FALLBACK_GENERAL,
    "extract":        settings.MODEL_FALLBACK_GENERAL,
    "profile":        settings.MODEL_FALLBACK_GENERAL,
    "q_behavioral":   settings.MODEL_FALLBACK_GENERAL,
    "q_technical":    settings.MODEL_FALLBACK_GENERAL,
    "eval":           settings.MODEL_FALLBACK_GENERAL,
    "eval_sysdesign": settings.MODEL_FALLBACK_REASONING,
    "feedback":       settings.MODEL_FALLBACK_GENERAL,
    "gap_analysis":   settings.MODEL_FALLBACK_REASONING,
}


class LLMRouter:
    async def call(
        self,
        task: str,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 500,
    ) -> str:
        if task not in TASK_ROUTES:
            raise ValueError(f"Unknown task: '{task}'. Valid: {list(TASK_ROUTES.keys())}")

        model, client = TASK_ROUTES[task]
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMError(f"Empty response from primary provider for task '{task}' (model={model})")
            return content

        except OpenAIError as primary_err:
            fallback_model = OPENROUTER_FALLBACKS[task]
            logger.warning(
                f"Groq failed for task '{task}' (model={model}): {primary_err}. "
                f"Trying OpenRouter fallback ({fallback_model})."
            )
            try:
                response = await openrouter_client.chat.completions.create(
                    model=fallback_model,
                    messages=messages,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if not content:
                    raise LLMError(f"Empty response from fallback provider for task '{task}' (model={fallback_model})")
                return content
            except OpenAIError as fallback_err:
                raise LLMError(
                    f"Both Groq and OpenRouter failed for task '{task}'. "
                    f"Groq: {primary_err}. OpenRouter: {fallback_err}"
                ) from fallback_err

    def parse_json_response(self, text: str) -> dict:
        import re
        cleaned = text.strip()
        # Strip <think>...</think> blocks (qwen3, deepseek-r1 thinking models).
        # Handle both complete blocks and truncated ones (no closing tag).
        cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL).strip()
        # If still starts with <think> (truncated — no closing tag), drop everything
        # up to the first JSON object/array that follows.
        if '<think>' in cleaned:
            cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL).strip()
        # Strip markdown fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        # Find first { or [ to skip any leading text
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            idx = cleaned.find(start_char)
            if idx != -1:
                last_idx = cleaned.rfind(end_char)
                if last_idx > idx:
                    cleaned = cleaned[idx:last_idx + 1]
                    break
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse LLM JSON response: {e}\nRaw: {text[:500]}"
            )


llm_router = LLMRouter()
