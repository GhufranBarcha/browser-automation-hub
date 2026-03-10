"""Pydantic schemas for API request/response."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import TaskStatus


class TaskEventOut(BaseModel):
    id: str
    event_type: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: str
    status: TaskStatus
    prompt_text: str
    pdf_filename: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    cancel_requested: bool
    attempt_count: int
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class TaskDetailOut(TaskOut):
    events: list[TaskEventOut] = Field(default_factory=list)


class QueueSummaryOut(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int
    total: int
    active_slots: int
    max_slots: int


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    email: str
    message: str = "Login successful"
