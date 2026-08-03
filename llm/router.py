import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import date
from time import monotonic

from openai import AsyncOpenAI, OpenAIError, RateLimitError

from config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


groq_client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url=settings.GROQ_BASE_URL,
)

nvidia_client = AsyncOpenAI(
    api_key=settings.NVIDIA_API_KEY or "unset",
    base_url=settings.NVIDIA_BASE_URL,
)

gemini_client = AsyncOpenAI(
    api_key=settings.GEMINI_API_KEY or "unset",
    base_url=settings.GEMINI_BASE_URL,
)

# Confirmed Groq free-tier daily caps; other models rely on reactive RateLimitError handling instead.
GROQ_8B_RPD = 14_400
GROQ_70B_VERSATILE_RPD = 1_000


@dataclass
class QuotaTracker:
    """In-process only — not safe for multi-worker/multi-pod."""

    max_rpm: int | None = None
    max_rpd: int | None = None
    _calls: list[float] = field(default_factory=list)
    _day: date = field(default_factory=date.today)
    _day_count: int = 0
    _exhausted_today: bool = False

    def _roll_day_if_needed(self) -> None:
        today = date.today()
        if today != self._day:
            self._day = today
            self._day_count = 0
            self._exhausted_today = False

    def available(self) -> bool:
        self._roll_day_if_needed()
        if self._exhausted_today:
            return False
        if self.max_rpd is not None and self._day_count >= self.max_rpd:
            return False
        if self.max_rpm is not None:
            now = monotonic()
            cutoff = now - 60
            self._calls = [t for t in self._calls if t > cutoff]
            if len(self._calls) >= self.max_rpm:
                return False
        return True

    def record_call(self) -> None:
        self._roll_day_if_needed()
        self._day_count += 1
        if self.max_rpm is not None:
            self._calls.append(monotonic())

    def mark_exhausted(self) -> None:
        self._roll_day_if_needed()
        self._exhausted_today = True


@dataclass
class ProviderSlot:
    name: str
    model: str
    client: AsyncOpenAI
    quota: QuotaTracker
    enabled: bool = True

    def available(self) -> bool:
        return self.enabled and self.quota.available()


_quota_registry: dict[tuple[str, str], QuotaTracker] = {}


def slot(
    provider: str,
    model: str,
    client: AsyncOpenAI,
    *,
    enabled: bool = True,
    max_rpm: int | None = None,
    max_rpd: int | None = None,
) -> ProviderSlot:
    """QuotaTrackers are shared across chains keyed by (provider, model)."""
    key = (provider, model)
    if key not in _quota_registry:
        _quota_registry[key] = QuotaTracker(max_rpm=max_rpm, max_rpd=max_rpd)
    return ProviderSlot(
        name=f"{provider}/{model}",
        model=model,
        client=client,
        quota=_quota_registry[key],
        enabled=enabled,
    )


_nvidia_enabled = bool(settings.NVIDIA_API_KEY)
_gemini_enabled = bool(settings.GEMINI_API_KEY)

TASK_CHAINS: dict[str, list[ProviderSlot]] = {
    "classify": [
        slot("groq", settings.MODEL_CLASSIFY, groq_client, max_rpd=GROQ_8B_RPD),
        slot("gemini", settings.MODEL_GEMMA4, gemini_client, enabled=_gemini_enabled),
        slot("nvidia", settings.MODEL_NIM_CLASSIFY, nvidia_client, enabled=_nvidia_enabled),
    ],
    "extract": [
        slot("nvidia", settings.MODEL_NIM_EXTRACT, nvidia_client, enabled=_nvidia_enabled),
        slot("gemini", settings.MODEL_GEMINI_FLASH_LITE, gemini_client, enabled=_gemini_enabled),
        slot("groq", settings.MODEL_EXTRACT, groq_client, max_rpd=GROQ_70B_VERSATILE_RPD),
    ],
    "eval": [
        slot("nvidia", settings.MODEL_NIM_REASONING, nvidia_client, enabled=_nvidia_enabled),
        slot("groq", settings.MODEL_EVAL, groq_client, max_rpd=GROQ_70B_VERSATILE_RPD),
    ],
    "eval_sysdesign": [
        slot("nvidia", settings.MODEL_NIM_REASONING, nvidia_client, enabled=_nvidia_enabled),
        slot("groq", settings.MODEL_EVAL_SYSDESIGN, groq_client),
    ],
    "feedback": [
        slot("nvidia", settings.MODEL_NIM_REASONING, nvidia_client, enabled=_nvidia_enabled),
        slot("gemini", settings.MODEL_GEMINI_FLASH_LITE, gemini_client, enabled=_gemini_enabled),
        slot("groq", settings.MODEL_FEEDBACK, groq_client, max_rpd=GROQ_70B_VERSATILE_RPD),
    ],
    "gap_analysis": [
        slot("groq", settings.MODEL_GAP_ANALYSIS, groq_client),
        slot("nvidia", settings.MODEL_NIM_CLASSIFY, nvidia_client, enabled=_nvidia_enabled),
    ],
}


def _retry_after_seconds(err: RateLimitError) -> float | None:
    response = getattr(err, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


class LLMRouter:
    async def call(
        self,
        task: str,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 500,
    ) -> str:
        if task not in TASK_CHAINS:
            raise ValueError(f"Unknown task: '{task}'. Valid: {list(TASK_CHAINS.keys())}")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        attempts: list[str] = []
        for provider in TASK_CHAINS[task]:
            if not provider.available():
                attempts.append(f"{provider.name} (skipped: quota exhausted or not configured)")
                continue

            try:
                response = await provider.client.chat.completions.create(
                    model=provider.model,
                    messages=messages,
                    max_tokens=max_tokens,
                )
                provider.quota.record_call()
                content = response.choices[0].message.content
                if not content:
                    raise LLMError(f"Empty response from {provider.name} for task '{task}'")
                return content

            except RateLimitError as err:
                provider.quota.mark_exhausted()
                retry_after = _retry_after_seconds(err)
                logger.warning(
                    f"[{task}] {provider.name} rate-limited, exhausted for today: {err}"
                )
                if retry_after:
                    await asyncio.sleep(min(retry_after, 5))
                attempts.append(f"{provider.name} (rate limited)")

            except OpenAIError as err:
                logger.warning(f"[{task}] {provider.name} failed: {err}")
                attempts.append(f"{provider.name} ({err})")

        raise LLMError(
            f"All providers exhausted or failed for task '{task}': {'; '.join(attempts)}"
        )

    def parse_json_response(self, text: str) -> dict:
        import re
        cleaned = text.strip()
        # Strip <think>...</think> blocks from reasoning models (qwen3, deepseek-r1).
        cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL).strip()
        if '<think>' in cleaned:  # truncated block, no closing tag
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
