from datetime import datetime

from pydantic import BaseModel, Field


class TodoItem(BaseModel):
    title: str
    assignee: str | None = None
    due_date: str | None = None
    description: str | None = None


class TaskCreate(BaseModel):
    title: str
    assignee: str | None = None
    due_date: str | None = None
    description: str | None = None
    source_platform: str | None = None
    source_user_id: str | None = None
    source_group_id: str | None = None


class TaskRecord(TaskCreate):
    id: int
    status: str = "pending"
    created_at: datetime
    updated_at: datetime


class TodoExtractionResult(BaseModel):
    todos: list[TodoItem] = Field(default_factory=list)
    summary: str | None = None

