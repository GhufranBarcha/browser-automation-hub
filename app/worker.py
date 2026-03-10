"""Background worker: polls DB for queued tasks and runs max MAX_CONCURRENCY at once."""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from app.automation_runner import run_automation
from app.config import MAX_CONCURRENCY
from app.database import AsyncSessionLocal
from app.models import Task, TaskEvent, TaskStatus

logger = logging.getLogger(__name__)

# Global state managed by the worker
_semaphore: asyncio.Semaphore | None = None
_active_slots: int = 0
# Maps task_id -> asyncio.Event (cancel flag)
_cancel_flags: dict[str, asyncio.Event] = {}


def get_active_slots() -> int:
    return _active_slots


def get_max_slots() -> int:
    return MAX_CONCURRENCY


def request_cancel(task_id: str) -> None:
    """Signal a running task to stop via its cancel event."""
    if task_id in _cancel_flags:
        _cancel_flags[task_id].set()


async def _log_event(task_id: str, event_type: str, message: str) -> None:
    async with AsyncSessionLocal() as db:
        event = TaskEvent(task_id=task_id, event_type=event_type, message=message)
        db.add(event)
        await db.commit()


async def _run_task(task: Task) -> None:
    """Execute one task, update DB before/after, enforce cancel flag."""
    global _active_slots
    task_id = task.id
    cancel_flag = asyncio.Event()
    _cancel_flags[task_id] = cancel_flag

    try:
        # Mark running
        async with AsyncSessionLocal() as db:
            db_task = await db.get(Task, task_id)
            if db_task is None:
                return
            db_task.status = TaskStatus.running
            db_task.started_at = datetime.utcnow()
            db_task.attempt_count = (db_task.attempt_count or 0) + 1
            await db.commit()

        await _log_event(task_id, "started", f"Automation started (attempt #{task.attempt_count + 1})")
        logger.info(f"[worker] Running task {task_id[-8:]}")

        # Live step callback — called by run_automation after each browser-use step.
        # Writes a "step" event to the DB so the Details page shows real-time progress.
        async def step_callback(step_num: int, goal: str, url: str | None) -> None:
            msg = f"Step {step_num}"
            if goal:
                msg += f": {goal}"
            if url:
                msg += f" ({url})"
            await _log_event(task_id, "step", msg)

        result = await run_automation(
            prompt=task.prompt_text,
            pdf_path=task.pdf_path,
            task_id=task_id,
            cancel_flag=cancel_flag,
            step_callback=step_callback,
        )

        # Check if cancel was requested (may have been set during run)
        async with AsyncSessionLocal() as db:
            db_task = await db.get(Task, task_id)
            if db_task is None:
                return

            if cancel_flag.is_set() or db_task.cancel_requested:
                db_task.status = TaskStatus.cancelled
                db_task.finished_at = datetime.utcnow()
                await db.commit()
                await _log_event(task_id, "cancelled", "Task was cancelled")
                logger.info(f"[worker] Task {task_id[-8:]} cancelled")
            elif result.success:
                db_task.status = TaskStatus.completed
                db_task.finished_at = datetime.utcnow()
                await db.commit()
                await _log_event(task_id, "completed", f"Automation completed successfully in {result.steps_taken} steps")
                logger.info(f"[worker] Task {task_id[-8:]} completed")
            else:
                db_task.status = TaskStatus.failed
                db_task.finished_at = datetime.utcnow()
                db_task.error_message = result.error
                await db.commit()
                await _log_event(task_id, "failed", f"Automation failed: {result.error}")
                logger.error(f"[worker] Task {task_id[-8:]} failed: {result.error}")

    except Exception as exc:
        logger.exception(f"[worker] Unexpected error for task {task_id[-8:]}: {exc}")
        try:
            async with AsyncSessionLocal() as db:
                db_task = await db.get(Task, task_id)
                if db_task:
                    db_task.status = TaskStatus.failed
                    db_task.finished_at = datetime.utcnow()
                    db_task.error_message = str(exc)
                    await db.commit()
            await _log_event(task_id, "failed", f"Unexpected error: {exc}")
        except Exception:
            pass
    finally:
        _cancel_flags.pop(task_id, None)
        _active_slots -= 1


async def _claim_and_run() -> bool:
    """Claim one queued task and schedule it. Returns True if a task was claimed."""
    global _active_slots

    async with AsyncSessionLocal() as db:
        # Pick oldest queued task
        result = await db.execute(
            select(Task)
            .where(Task.status == TaskStatus.queued)
            .order_by(Task.created_at.asc())
            .limit(1)
        )
        task = result.scalar_one_or_none()
        if task is None:
            return False

        # Check it hasn't been removed/cancelled between poll and claim
        if task.cancel_requested:
            task.status = TaskStatus.cancelled
            task.finished_at = datetime.utcnow()
            await db.commit()
            return False

        # Optimistically mark (prevents double-claim on fast polls)
        task.status = TaskStatus.running
        task.started_at = datetime.utcnow()
        await db.commit()
        # Reload to get full object for the async task
        task_id = task.id

    _active_slots += 1
    # Schedule task execution without blocking the dispatcher
    asyncio.create_task(_run_task_by_id(task_id))
    return True


async def _run_task_by_id(task_id: str) -> None:
    """Reload task from DB and execute under semaphore."""
    assert _semaphore is not None
    async with _semaphore:
        async with AsyncSessionLocal() as db:
            task = await db.get(Task, task_id)
            if task is None:
                return
            # Reset to queued so _run_task can properly set running + timestamp
            task.status = TaskStatus.queued
            task.started_at = None
            await db.commit()
        await _run_task(task)


async def dispatcher_loop() -> None:
    """Main worker loop: runs as a background asyncio task inside FastAPI lifespan."""
    global _semaphore, _active_slots
    _semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    _active_slots = 0
    logger.info(f"[worker] Dispatcher started — max concurrency = {MAX_CONCURRENCY}")

    # On startup, recover any tasks stuck in "running" state (process restart)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Task).where(Task.status == TaskStatus.running))
        stuck = result.scalars().all()
        for task in stuck:
            task.status = TaskStatus.queued
            task.started_at = None
            logger.warning(f"[worker] Recovering stuck task {task.id[-8:]}")
        if stuck:
            await db.commit()
            logger.info(f"[worker] Recovered {len(stuck)} stuck tasks")

    while True:
        try:
            # Poll for queued tasks — fill up to MAX_CONCURRENCY slots
            slots_available = MAX_CONCURRENCY - _active_slots
            for _ in range(slots_available):
                claimed = await _claim_and_run()
                if not claimed:
                    break  # No more queued tasks right now
        except Exception as exc:
            logger.exception(f"[worker] Dispatcher error: {exc}")

        await asyncio.sleep(2)  # Poll every 2 seconds
