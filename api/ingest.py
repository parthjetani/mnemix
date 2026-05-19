import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database import IngestionJobORM, get_db
from core.auth import get_current_user
from llm.embeddings import embed
from core.ingestion.resume_parser import parse_resume
from core.ingestion.chatgpt_parser import parse_chatgpt_export
from core.ingestion.claude_parser import parse_claude_export
from core.processing.segmenter import segment
from core.processing.extractor import process_ingestion_pipeline
from core.memory.store import save_memory
from core.memory.retriever import memory_retriever
from models.schemas import IngestResponse

import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/ingest", tags=["ingest"])

MAX_RESUME_BYTES = 50 * 1024 * 1024    # 50 MB
MAX_EXPORT_BYTES = 200 * 1024 * 1024   # 200 MB


def _save_upload_with_limit(upload: UploadFile, suffix: str, max_bytes: int) -> Path:
    """Copy the upload to a temp file, aborting if it exceeds max_bytes."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    written = 0
    try:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                tmp.close()
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail={"error": f"File too large (max {max_bytes // (1024*1024)} MB)"},
                )
            tmp.write(chunk)
    finally:
        tmp.close()
    return Path(tmp.name)


async def _run_resume_ingestion(job_id: str, temp_path: Path) -> None:
    from database import async_session_factory
    async with async_session_factory() as db:
        try:
            job = await db.get(IngestionJobORM, job_id)
            if not job:
                return

            job.status = "processing"
            job.progress = 10
            await db.flush()

            result = await parse_resume(temp_path)
            raw_memories = result.get("raw_memories", [])

            saved = 0
            for mem in raw_memories:
                embedding = embed(mem.content)
                mid = await save_memory(mem, embedding, db)
                await memory_retriever.add_to_index(mid, embedding)
                saved += 1

            job.status = "complete"
            job.progress = 100
            job.memories_found = saved
            await db.commit()
        except Exception as e:
            await db.rollback()
            async with async_session_factory() as err_db:
                job = await err_db.get(IngestionJobORM, job_id)
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    await err_db.commit()
        finally:
            temp_path.unlink(missing_ok=True)


async def _run_ai_export_ingestion(job_id: str, temp_path: Path, source_type: str) -> None:
    from database import async_session_factory
    async with async_session_factory() as db:
        try:
            job = await db.get(IngestionJobORM, job_id)
            if not job:
                return

            if source_type == "chatgpt":
                conversations = await parse_chatgpt_export(temp_path)
            else:
                conversations = await parse_claude_export(temp_path)

            all_segments = []
            for conv in conversations:
                segs = await segment([conv])
                all_segments.extend(segs)

            job.status = "processing"
            job.progress = 20
            await db.flush()

            _count, memories = await process_ingestion_pipeline(all_segments, job_id, db)

            saved = 0
            for mem in memories:
                embedding = embed(mem.content)
                mid = await save_memory(mem, embedding, db)
                await memory_retriever.add_to_index(mid, embedding)
                saved += 1

            job.status = "complete"
            job.progress = 100
            job.memories_found = saved
            await db.commit()
        except Exception as e:
            await db.rollback()
            async with async_session_factory() as err_db:
                job = await err_db.get(IngestionJobORM, job_id)
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    await err_db.commit()
        finally:
            temp_path.unlink(missing_ok=True)


@router.post("/resume", response_model=IngestResponse)
async def ingest_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    if file.size is not None and file.size > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"error": f"Resume too large (max {MAX_RESUME_BYTES // (1024*1024)} MB)"},
        )

    suffix = Path(file.filename).suffix
    temp_path = _save_upload_with_limit(file, suffix, MAX_RESUME_BYTES)

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    job = IngestionJobORM(
        id=job_id,
        source_type="resume",
        status="queued",
        progress=0,
        created_at=now,
    )
    db.add(job)
    await db.commit()   # commit before background task so it can see the row

    background_tasks.add_task(_run_resume_ingestion, job_id, temp_path)

    return IngestResponse(job_id=job_id, status="queued", message="Resume ingestion started")


@router.post("/ai-export", response_model=IngestResponse)
async def ingest_ai_export(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    if source_type not in ("chatgpt", "claude"):
        raise HTTPException(status_code=400, detail="source_type must be 'chatgpt' or 'claude'")

    if file.size is not None and file.size > MAX_EXPORT_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"error": f"Export too large (max {MAX_EXPORT_BYTES // (1024*1024)} MB)"},
        )

    filename = file.filename or "export.zip"
    suffix = Path(filename).suffix or ".zip"
    temp_path = _save_upload_with_limit(file, suffix, MAX_EXPORT_BYTES)

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    job = IngestionJobORM(
        id=job_id,
        source_type=source_type,
        status="queued",
        progress=0,
        created_at=now,
    )
    db.add(job)
    await db.commit()   # commit before background task so it can see the row

    background_tasks.add_task(_run_ai_export_ingestion, job_id, temp_path, source_type)

    return IngestResponse(job_id=job_id, status="queued", message=f"{source_type} export ingestion started")


@router.get("/jobs")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(
        select(IngestionJobORM).order_by(IngestionJobORM.created_at.desc())
    )
    jobs = result.scalars().all()
    return [
        {
            "job_id": j.id,
            "id": j.id,
            "status": j.status,
            "progress": j.progress,
            "memories_found": j.memories_found,
            "source_type": j.source_type,
            "total_segments": j.total_segments,
            "processed": j.processed,
            "started_at": j.started_at,
            "completed_at": j.completed_at,
            "error_message": j.error_message,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


@router.get("/status/{job_id}")
async def get_ingest_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    job = await db.get(IngestionJobORM, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "memories_found": job.memories_found,
        "source_type": job.source_type,
        "error_message": job.error_message,
    }
