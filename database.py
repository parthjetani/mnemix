import asyncio
import ssl
from sqlalchemy import (
    Column, Text, Integer, Float, LargeBinary, Boolean,
    ForeignKey, String, text,
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings


_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"ssl": _ssl_ctx},
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
async_session_factory = AsyncSessionLocal   # alias for background tasks


class Base(DeclarativeBase):
    pass


class MemoryORM(Base):
    __tablename__ = "memories"

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=True, index=True)   # Planted for multi-user. Not enforced yet.
    content = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    themes = Column(Text, default="[]")            # JSON array as text
    interview_qs = Column(Text, default="[]")      # JSON array as text
    confidence = Column(Float, default=0.0)
    source = Column(Text)
    date_context = Column(Text)
    has_outcome = Column(Boolean, default=False)
    outcome_quantified = Column(Boolean, default=False)
    embedding = Column(LargeBinary)                # numpy array serialized
    created_at = Column(Text)
    access_count = Column(Integer, default=0)
    last_accessed = Column(Text)


class InterviewSessionORM(Base):
    __tablename__ = "interview_sessions"

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=True, index=True)   # Planted for multi-user. Not enforced yet.
    started_at = Column(Text)
    completed_at = Column(Text)
    session_type = Column(Text)
    overall_score = Column(Float)
    status = Column(Text, default="in_progress")
    questions_list = Column(Text)                  # JSON array of question dicts
    feedback_report = Column(Text)                 # Final LLM-generated report text


class SessionAnswerORM(Base):
    __tablename__ = "session_answers"

    id = Column(Text, primary_key=True)
    session_id = Column(Text, ForeignKey("interview_sessions.id"))
    question_id = Column(Text)
    question_text = Column(Text)
    answer_text = Column(Text)
    answer_order = Column(Integer)
    memory_match_score = Column(Float)
    specificity_score = Column(Float)
    outcome_stated = Column(Boolean)
    outcome_quantified = Column(Boolean)
    coherence_score = Column(Float)
    memory_opportunity = Column(Text)
    total_score = Column(Float)
    feedback_text = Column(Text)
    created_at = Column(Text)


class QuestionORM(Base):
    __tablename__ = "questions"

    id = Column(Text, primary_key=True)
    text = Column(Text, nullable=False)
    category = Column(Text)
    field = Column(Text)
    seniority = Column(Text)
    source = Column(Text, default="seeded")
    effectiveness_score = Column(Float, default=0.5)
    use_count = Column(Integer, default=0)
    created_at = Column(Text)


class IngestionJobORM(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=True, index=True)   # Planted for multi-user. Not enforced yet.
    source_type = Column(Text)
    status = Column(Text, default="pending")
    progress = Column(Integer, default=0)
    total_segments = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    memories_found = Column(Integer, default=0)
    created_at = Column(Text)
    started_at = Column(Text)
    completed_at = Column(Text)
    error_message = Column(Text)


class UserProfileORM(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, default=1)
    field = Column(Text, default="software_engineering")
    seniority = Column(Text, default="mid")
    primary_stack = Column(Text, default="[]")     # JSON array as text
    target_roles = Column(Text, default="[]")      # JSON array as text
    communication_style = Column(Text)
    strength_areas = Column(Text, default="[]")    # JSON array as text
    gap_areas = Column(Text, default="[]")         # JSON array as text
    career_narrative = Column(Text)
    last_updated = Column(Text)


_USER_ID_MIGRATIONS = (
    "ALTER TABLE memories ADD COLUMN IF NOT EXISTS user_id TEXT",
    "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS user_id TEXT",
    "ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS user_id TEXT",
    "CREATE INDEX IF NOT EXISTS memories_user_id_idx ON memories (user_id)",
    "CREATE INDEX IF NOT EXISTS interview_sessions_user_id_idx ON interview_sessions (user_id)",
    "CREATE INDEX IF NOT EXISTS ingestion_jobs_user_id_idx ON ingestion_jobs (user_id)",
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent migration: plant user_id on pre-existing tables.
        for stmt in _USER_ID_MIGRATIONS:
            await conn.execute(text(stmt))


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(init_db())
    print("Tables created successfully.")
    print("Database:", settings.DATABASE_URL)
