import re
import json
from pathlib import Path

import fitz  # pymupdf

from llm.router import llm_router, LLMError
from llm.prompts import EXTRACTION_PROMPT
from models.schemas import MemoryCreate


_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.\w+')
_PHONE_RE = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')
_URL_RE = re.compile(r'https?://\S+|www\.\S+')
_LINKEDIN_RE = re.compile(r'linkedin\.com/\S+', re.IGNORECASE)


def _extract_text(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def _anonymize(text: str) -> str:
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _LINKEDIN_RE.sub("[LINKEDIN]", text)
    text = _URL_RE.sub("[URL]", text)
    return text


async def parse_resume(file_path: Path) -> dict:
    raw_text = _extract_text(file_path)
    clean_text = _anonymize(raw_text)

    prompt = EXTRACTION_PROMPT.format(
        field="software_engineering",
        role="software engineer",
        user_messages=clean_text[:6000],  # stay within token limits
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
        except Exception:
            continue

    return {
        "raw_text_length": len(raw_text),
        "raw_memories": memories,
    }
