import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database import IngestionJobORM, get_db
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


async def _run_resume_ingestion(job_id: str, temp_path: Path) -> None:
    from database import async_session_factory
    async with async_session_factory() as db:
        try:
            result = await parse_resume(temp_path)
            raw_memories = result.get("raw_memories", [])

            job_result = await db.get(IngestionJobORM, job_id)
            if job_result:
                job_result.status = "processing"
                job_result.progress = 10
                await db.flush()

            saved = 0
            for mem in raw_memories:
                embedding = embed(mem.content)
                mid = await save_memory(mem, embedding, db)
                await memory_retriever.add_to_index(mid, embedding)
                saved += 1

            await db.flush()

            job_result = await db.get(IngestionJobORM, job_id)
            if job_result:
                job_result.status = "complete"
                job_result.progress = 100
                job_result.memories_found = saved
                await db.flush()

            await db.commit()
        except Exception as e:
            await db.rollback()
            job_result = await db.get(IngestionJobORM, job_id)
            if job_result:
                job_result.status = "failed"
                job_result.error_message = str(e)
                await db.flush()
                await db.commit()
        finally:
            temp_path.unlink(missing_ok=True)


async def _run_ai_export_ingestion(job_id: str, temp_path: Path, source_type: str) -> None:
    from database import async_session_factory
    async with async_session_factory() as db:
        try:
            if source_type == "chatgpt":
                conversations = await parse_chatgpt_export(temp_path)
            else:
                conversations = await parse_claude_export(temp_path)

            all_segments = []
            for conv in conversations:
                segs = await segment([conv])
                all_segments.extend(segs)

            job_result = await db.get(IngestionJobORM, job_id)
            if job_result:
                job_result.status = "processing"
                job_result.progress = 20
                await db.flush()

            total_saved, memories = await process_ingestion_pipeline(all_segments, job_id, db)

            for mem in memories:
                embedding = embed(mem.content)
                mid = await save_memory(mem, embedding, db)
                await memory_retriever.add_to_index(mid, embedding)

            job_result = await db.get(IngestionJobORM, job_id)
            if job_result:
                job_result.status = "complete"
                job_result.progress = 100
                job_result.memories_found = total_saved
                await db.flush()

            await db.commit()
        except Exception as e:
            await db.rollback()
            job_result = await db.get(IngestionJobORM, job_id)
            if job_result:
                job_result.status = "failed"
                job_result.error_message = str(e)
                await db.flush()
                await db.commit()
        finally:
            temp_path.unlink(missing_ok=True)


@router.post("/resume", response_model=IngestResponse)
async def ingest_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

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
    await db.flush()

    suffix = Path(file.filename).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp)
    tmp.close()
    temp_path = Path(tmp.name)

    background_tasks.add_task(_run_resume_ingestion, job_id, temp_path)

    return IngestResponse(job_id=job_id, status="queued", message="Resume ingestion started")


@router.post("/ai-export", response_model=IngestResponse)
async def ingest_ai_export(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if source_type not in ("chatgpt", "claude"):
        raise HTTPException(status_code=400, detail="source_type must be 'chatgpt' or 'claude'")

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
    await db.flush()

    filename = file.filename or f"export.{'zip' if source_type == 'chatgpt' else 'zip'}"
    suffix = Path(filename).suffix or ".zip"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp)
    tmp.close()
    temp_path = Path(tmp.name)

    background_tasks.add_task(_run_ai_export_ingestion, job_id, temp_path, source_type)

    return IngestResponse(job_id=job_id, status="queued", message=f"{source_type} export ingestion started")


@router.get("/status/{job_id}")
async def get_ingest_status(job_id: str, db: AsyncSession = Depends(get_db)):
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
