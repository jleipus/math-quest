from threading import Lock

from backend.models.game import Task


class TaskRegistry:
    """Stores previosuly generated tasks."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks: dict[str, Task] = {}

    def put(self, tasks: list[Task]) -> None:
        with self._lock:
            for task in tasks:
                self._tasks[str(task.task_id)] = task

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)


task_registry = TaskRegistry()
