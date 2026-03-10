"""SQLAlchemy ORM models."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    removed = "removed"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.queued, index=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    events: Mapped[list["TaskEvent"]] = relationship(
        "TaskEvent", back_populates="task", cascade="all, delete-orphan", order_by="TaskEvent.created_at"
    )


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # queued/started/completed/failed/cancelled/info
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped["Task"] = relationship("Task", back_populates="events")
