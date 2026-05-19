import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from llm.router import llm_router, LLMError
from llm.prompts import EXTRACTION_PROMPT
from models.schemas import MemoryCreate
from core.processing.classifier import classify, PROFESSIONAL_KEYWORDS
from core.processing.anonymize import escape_braces

logger = logging.getLogger(__name__)


def _filter_professional_sentences(messages: list[str]) -> list[str]:
    """For MIXED segments — keep only sentences containing professional signals."""
    filtered = []
    for msg in messages:
        sentences = [s.strip() for s in msg.replace("\n", ". ").split(".") if s.strip()]
        pro_sentences = [
            s for s in sentences
            if any(kw in s.lower() for kw in PROFESSIONAL_KEYWORDS)
        ]
        if pro_sentences:
            filtered.append(". ".join(pro_sentences))
    return filtered


async def extract_memories(
    segment: dict,
    field: str = "software_engineering",
) -> list[MemoryCreate]:
    classification = segment.get("classification") or await classify(segment)

    if classification == "PERSONAL":
        return []

    if classification == "MIXED":
        messages = _filter_professional_sentences(segment.get("messages", []))
    else:
        messages = segment.get("messages", [])

    if not messages:
        return []

    user_messages_text = "\n---\n".join(messages)
    # Truncate to avoid hitting token limits on Groq
    user_messages_text = user_messages_text[:4000]

    prompt = EXTRACTION_PROMPT.format(
        field=field,
        role="software engineer",
        user_messages=escape_braces(user_messages_text),
    )

    try:
        result = await llm_router.call("extract", prompt, max_tokens=1000)
        parsed = llm_router.parse_json_response(result)
        raw_memories = parsed.get("memories", [])
    except (LLMError, ValueError) as e:
        if settings.DEBUG:
            logger.debug(f"Extraction failed for segment {segment.get('segment_index')}: {e}")
        return []

    memories: list[MemoryCreate] = []
    for m in raw_memories:
        try:
            confidence = float(m.get("confidence", 0.0))
            if confidence < settings.MIN_CONFIDENCE_THRESHOLD:
                logger.debug(
                    f"Memory dropped (confidence {confidence} < threshold "
                    f"{settings.MIN_CONFIDENCE_THRESHOLD}): {str(m.get('content', ''))[:80]}"
                )
                continue
            memories.append(MemoryCreate(
                content=m.get("content", ""),
                category=m.get("category", "technical_achievement"),
                themes=m.get("themes", []),
                interview_qs=m.get("interview_qs", []),
                confidence=confidence,
                source=segment.get("source", "unknown"),
                date_context=m.get("date_context"),
                has_outcome=bool(m.get("has_outcome", False)),
                outcome_quantified=bool(m.get("outcome_quantified", False)),
            ))
        except Exception as e:
            logger.debug(f"Memory dropped (validation failed: {e}): {str(m)[:120]}")
            continue

    return memories


async def process_ingestion_pipeline(
    segments: list[dict],
    job_id: str,
    db: AsyncSession,
    field: str = "software_engineering",
) -> tuple[int, list[MemoryCreate]]:
    """
    Classify all segments, then extract memories in batches with rate-limit delay.
    Updates the IngestionJob record progress during extraction.
    Returns (count, memories) — caller is responsible for saving to DB and completing the job.
    """
    from database import IngestionJobORM
    from sqlalchemy import select

    # Update job: set total_segments
    result = await db.execute(select(IngestionJobORM).where(IngestionJobORM.id == job_id))
    job = result.scalar_one_or_none()
    if job:
        job.total_segments = len(segments)
        job.status = "processing"
        await db.flush()

    # Step 1: classify all segments (fast, rule-based mostly)
    for seg in segments:
        seg["classification"] = await classify(seg)

    professional_segs = [
        s for s in segments
        if s["classification"] in ("PROFESSIONAL", "BEHAVIORAL_PRO", "MIXED")
    ]

    # Step 2: extract in batches (respects Groq 6K TPM limit)
    all_memories: list[MemoryCreate] = []
    batch_size = settings.EXTRACTION_BATCH_SIZE
    delay = settings.EXTRACTION_BATCH_DELAY

    for i in range(0, len(professional_segs), batch_size):
        batch = professional_segs[i:i + batch_size]
        tasks = [extract_memories(seg, field=field) for seg in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, list):
                all_memories.extend(res)

        # Update progress
        if job:
            processed = min(i + batch_size, len(professional_segs))
            job.processed = processed
            job.memories_found = len(all_memories)
            await db.flush()

        # Rate limit delay between batches (skip after last batch)
        if i + batch_size < len(professional_segs):
            await asyncio.sleep(delay)

    return len(all_memories), all_memories
