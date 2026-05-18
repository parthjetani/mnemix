from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from database import init_db, get_db
from llm.embeddings import embed
from core.interview.question_bank import load_questions
from core.memory.retriever import memory_retriever
from api.ingest import router as ingest_router
from api.memory import router as memory_router
from api.interview import router as interview_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await load_questions(db)
        await db.commit()
        await memory_retriever.load(db)
    embed("warmup")
    yield


app = FastAPI(
    title="MNEMIX",
    version="0.1.0",
    description="Memory-Powered Interview Coach",
    lifespan=lifespan,
)

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
