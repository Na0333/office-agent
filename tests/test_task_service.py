from app.schemas.task import TaskCreate
from app.services.task_service import TaskService


def test_create_task():
    service = TaskService()
    task = service.create_task(TaskCreate(title="完成项目框架"))
    assert task["id"] > 0
    assert task["title"] == "完成项目框架"

