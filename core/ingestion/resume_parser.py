import logging
from pathlib import Path

import fitz  # pymupdf

from llm.router import llm_router, LLMError
from llm.prompts import EXTRACTION_PROMPT
from models.schemas import MemoryCreate
from core.processing.anonymize import anonymize, escape_braces

logger = logging.getLogger(__name__)


def _extract_text(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


async def parse_resume(file_path: Path) -> dict:
    raw_text = _extract_text(file_path)
    clean_text = anonymize(raw_text)

    prompt = EXTRACTION_PROMPT.format(
        field="software_engineering",
        role="software engineer",
        user_messages=escape_braces(clean_text[:6000]),  # stay within token limits
    )

    try:
        result = await llm_router.call("extract", prompt, max_tokens=1500)
        parsed = llm_router.parse_json_response(result)
        raw_memories = parsed.get("memories", [])
    except (LLMError, ValueError):
        raw_memories = []

    memories: list[MemoryCreate] = []
    for m in raw_memories:
        try:
            memories.append(MemoryCreate(
                content=m.get("content", ""),
                category=m.get("category", "technical_achievement"),
                themes=m.get("themes", []),
                interview_qs=m.get("interview_qs", []),
                confidence=float(m.get("confidence", 0.0)),
                source="resume",
                date_context=m.get("date_context"),
                has_outcome=bool(m.get("has_outcome", False)),
                outcome_quantified=bool(m.get("outcome_quantified", False)),
            ))
        except Exception as e:
            logger.debug(f"Resume memory dropped: {e}")
            continue

    return {
        "raw_text_length": len(raw_text),
        "raw_memories": memories,
    }
