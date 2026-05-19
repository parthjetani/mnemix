import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from core.logging_config import configure_logging, configure_sentry
from core.rate_limit import limiter
from database import init_db, get_db

configure_logging(settings.LOG_LEVEL)
configure_sentry()
from llm.embeddings import embed
from core.interview.question_bank import load_questions
from core.memory.retriever_pgvector import memory_retriever
from api.ingest import router as ingest_router
from api.memory import router as memory_router
from api.interview import router as interview_router
from api.profile import router as profile_router
from api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await load_questions(db)
        await db.commit()
    embed("warmup")
    yield


app = FastAPI(
    title="MNEMIX",
    version="0.1.0",
    description="Memory-Powered Interview Coach",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(ingest_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/config.js")
async def frontend_config():
    """Server-rendered frontend config so Supabase URL/anon-key live in one place,
    not duplicated across every HTML file."""
    body = (
        "window.MNEMIX_CONFIG = "
        + _json_encode({
            "supabase": {
                "url": settings.SUPABASE_URL,
                "anonKey": settings.SUPABASE_ANON_KEY,
            },
        })
        + ";\n"
    )
    return Response(content=body, media_type="application/javascript")


def _json_encode(obj):
    import json
    return json.dumps(obj)


# Serve frontend — must be after all API routes
_frontend_dir = Path(__file__).parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="static")
