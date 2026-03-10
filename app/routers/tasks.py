"""Tasks API router: CRUD, actions, queue summary."""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select

from app import worker
from app.auth import get_current_user
from app.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.database import AsyncSessionLocal, get_db
from app.models import Task, TaskEvent, TaskStatus
from app.schemas import QueueSummaryOut, TaskDetailOut, TaskOut

router = APIRouter(prefix="/api", tags=["tasks"])

ALLOWED_MIME = {"application/pdf"}


async def _add_event(task_id: str, event_type: str, message: str) -> None:
    async with AsyncSessionLocal() as db:
        event = TaskEvent(task_id=task_id, event_type=event_type, message=message)
        db.add(event)
        await db.commit()


# ── Create Task ─────────────────────────────────────────────────────────
@router.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(
    prompt: str = Form(..., description="Full automation instruction"),
    file: Optional[UploadFile] = File(None, description="PDF file to upload"),
    user: dict = Depends(get_current_user),
):
    # Validate file if provided
    pdf_path: str | None = None
    pdf_filename: str | None = None

    if file and file.filename:
        if file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")

        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"File too large (max {MAX_UPLOAD_BYTES // 1024 // 1024} MB)")

        # Safe filename — never trust user input
        safe_name = f"{uuid.uuid4().hex}.pdf"
        dest = UPLOAD_DIR / safe_name
        dest.write_bytes(content)
        pdf_path = str(dest)
        pdf_filename = file.filename

    async with AsyncSessionLocal() as db:
        task = Task(
            id=str(uuid.uuid4()),
            prompt_text=prompt,
            pdf_path=pdf_path,
            pdf_filename=pdf_filename,
            status=TaskStatus.queued,
            created_by=user.get("email"),
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        task_id = task.id

    await _add_event(task_id, "queued", "Task added to queue")
    return task


# ── List Tasks ──────────────────────────────────────────────────────────
@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 200,
    user: dict = Depends(get_current_user),
):
    async with AsyncSessionLocal() as db:
        q = select(Task).order_by(Task.created_at.desc()).limit(limit)
        if status:
            try:
                q = q.where(Task.status == TaskStatus(status))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Unknown status: {status}")
        result = await db.execute(q)
        return result.scalars().all()


# ── Task Detail ─────────────────────────────────────────────────────────
@router.get("/tasks/{task_id}", response_model=TaskDetailOut)
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        # Eagerly load events
        result = await db.execute(
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id)
            .order_by(TaskEvent.created_at.asc())
        )
        events = result.scalars().all()
        # Build response manually to include events
        detail = TaskDetailOut.model_validate(task)
        detail.events = [e for e in events]
        return detail


# ── Cancel Task ─────────────────────────────────────────────────────────
@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status not in (TaskStatus.queued, TaskStatus.running):
            raise HTTPException(status_code=400, detail=f"Cannot cancel task in status '{task.status}'")

        task.cancel_requested = True
        if task.status == TaskStatus.queued:
            task.status = TaskStatus.cancelled
            task.finished_at = datetime.utcnow()
        await db.commit()

    # Signal worker if running
    worker.request_cancel(task_id)
    await _add_event(task_id, "cancelled", f"Cancellation requested by {user.get('email')}")
    return {"message": "Cancel requested"}


# ── Remove Task ─────────────────────────────────────────────────────────
@router.delete("/tasks/{task_id}")
async def remove_task(task_id: str, user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status == TaskStatus.running:
            raise HTTPException(status_code=400, detail="Cannot delete a running task — cancel it first")

        # Delete uploaded PDF if present
        if task.pdf_path and Path(task.pdf_path).is_file():
            try:
                os.remove(task.pdf_path)
            except OSError:
                pass

        await db.delete(task)
        await db.commit()
    return {"message": "Task deleted"}


# ── Retry Task ──────────────────────────────────────────────────────────
@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str, user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status not in (TaskStatus.failed, TaskStatus.cancelled):
            raise HTTPException(status_code=400, detail=f"Cannot retry task in status '{task.status}'")

        task.status = TaskStatus.queued
        task.cancel_requested = False
        task.error_message = None
        task.started_at = None
        task.finished_at = None
        await db.commit()

    await _add_event(task_id, "queued", f"Task re-queued for retry by {user.get('email')}")
    return {"message": "Task re-queued"}


# ── Queue Summary ───────────────────────────────────────────────────────
@router.get("/queue/summary", response_model=QueueSummaryOut)
async def queue_summary(user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        )
        counts = {row[0]: row[1] for row in result.all()}

    return QueueSummaryOut(
        queued=counts.get(TaskStatus.queued, 0),
        running=counts.get(TaskStatus.running, 0),
        completed=counts.get(TaskStatus.completed, 0),
        failed=counts.get(TaskStatus.failed, 0),
        cancelled=counts.get(TaskStatus.cancelled, 0),
        total=sum(counts.values()),
        active_slots=worker.get_active_slots(),
        max_slots=worker.get_max_slots(),
    )
