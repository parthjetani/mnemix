import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from core.auth import get_current_user
from core.memory.retriever import memory_retriever
from llm.router import llm_router, LLMError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    memories_used: list[dict]


CHAT_SYSTEM = (
    "You are an expert interview coach with deep knowledge of the user's professional history. "
    "Answer questions using the specific memories and experiences provided. "
    "Be direct, concrete, and reference specific details from their history when possible. "
    "If asked to help practice an answer, use their actual experiences rather than generic examples."
)


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail={"error": "Message cannot be empty"})

    # Retrieve relevant memories
    try:
        top_memories = await memory_retriever.search(req.message, db, top_k=5)
    except Exception as e:
        logger.warning(f"Memory retrieval failed: {e}")
        top_memories = []

    # Build context from memories
    memory_context = ""
    memories_used = []
    if top_memories:
        memory_lines = []
        for mem, score in top_memories:
            if score > 0.25:  # only include relevant memories
                memory_lines.append(f"- [{mem.category}] {mem.content}")
                memories_used.append({"id": mem.id, "category": mem.category, "score": round(score, 3)})
        if memory_lines:
            memory_context = "\n\nRelevant memories from your history:\n" + "\n".join(memory_lines)

    prompt = f"{req.message}{memory_context}"

    try:
        response_text = await llm_router.call(
            task="feedback",
            prompt=prompt,
            system=CHAT_SYSTEM,
            max_tokens=800,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

    return ChatResponse(response=response_text, memories_used=memories_used)
