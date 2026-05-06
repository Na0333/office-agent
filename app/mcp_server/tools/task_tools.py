from app.schemas.task import TaskCreate
from app.services.task_service import TaskService


def create_tasks(
    todos: list[dict],
    source_platform: str | None = None,
    source_user_id: str | None = None,
    source_group_id: str | None = None,
) -> dict:
    service = TaskService()
    created = []
    for todo in todos:
        task = TaskCreate(
            title=todo.get("title", "未命名任务"),
            assignee=todo.get("assignee"),
            due_date=todo.get("due_date"),
            description=todo.get("description"),
            source_platform=source_platform,
            source_user_id=source_user_id,
            source_group_id=source_group_id,
        )
        created.append(service.create_task(task))
    return {"created_count": len(created), "tasks": created}


def query_task_status(user_id: str | None = None) -> dict:
    service = TaskService()
    return {"tasks": service.list_tasks(source_user_id=user_id)}

