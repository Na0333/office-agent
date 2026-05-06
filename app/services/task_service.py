from datetime import datetime
from typing import Any

from app.database.db import get_connection, init_db
from app.schemas.task import TaskCreate


class TaskService:
    def __init__(self) -> None:
        init_db()

    def create_task(self, task: TaskCreate) -> dict[str, Any]:
        now = datetime.now().isoformat(timespec="seconds")
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    title, description, assignee, due_date, status,
                    source_platform, source_user_id, source_group_id,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.title,
                    task.description,
                    task.assignee,
                    task.due_date,
                    "pending",
                    task.source_platform,
                    task.source_user_id,
                    task.source_group_id,
                    now,
                    now,
                ),
            )
            conn.commit()
            task_id = cursor.lastrowid
        return {"id": task_id, "title": task.title, "assignee": task.assignee, "due_date": task.due_date, "status": "pending"}

    def list_tasks(self, source_user_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM tasks"
        params: tuple[Any, ...] = ()
        if source_user_id:
            sql += " WHERE source_user_id = ?"
            params = (source_user_id,)
        sql += " ORDER BY id DESC LIMIT 20"

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

