from datetime import datetime, timezone
from enum import Enum
import json
import threading
import uuid
from pathlib import Path
from typing import Any, Callable

from src.utils.config import Settings, get_settings
from src.utils.logging import get_logger

logger = get_logger("utils.tasks")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskManager:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.settings.task_store_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._job_lock = threading.Lock()
        self._load_tasks()

    def _task_path(self, task_id: str) -> Path:
        return self.settings.task_store_dir / f"{task_id}.json"

    def _load_tasks(self) -> None:
        for path in self.settings.task_store_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._tasks[data["task_id"]] = data
            except (json.JSONDecodeError, KeyError):
                continue

    def _save_task(self, task_id: str) -> None:
        task = self._tasks[task_id]
        self._task_path(task_id).write_text(
            json.dumps(task, indent=2, default=str), encoding="utf-8"
        )

    def create_task(self, task_type: str, **metadata: Any) -> str:
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        task = {
            "task_id": task_id,
            "type": task_type,
            "status": TaskStatus.PENDING.value,
            "progress": {
                "step": "queued",
                "current": 0,
                "total": 0,
                "percent": 0.0,
            },
            "started_at": now,
            "completed_at": None,
            "error": None,
            "result": None,
            **metadata,
        }
        with self._lock:
            self._tasks[task_id] = task
            self._save_task(task_id)
        logger.info("Task created | task_id=%s type=%s", task_id, task_type)
        return task_id

    def update_progress(
        self, task_id: str, step: str, current: int, total: int
    ) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            percent = round((current / total) * 100, 1) if total else 0.0
            task["status"] = TaskStatus.RUNNING.value
            task["progress"] = {
                "step": step,
                "current": current,
                "total": total,
                "percent": percent,
            }
            self._save_task(task_id)

    def mark_running(self, task_id: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task["status"] = TaskStatus.RUNNING.value
            self._save_task(task_id)

    def complete(self, task_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task["status"] = TaskStatus.COMPLETED.value
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task["result"] = result
            task["progress"] = {
                "step": "done",
                "current": task["progress"].get("total", 0),
                "total": task["progress"].get("total", 0),
                "percent": 100.0,
            }
            self._save_task(task_id)
        logger.info("Task completed | task_id=%s", task_id)

    def fail(self, task_id: str, error: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task["status"] = TaskStatus.FAILED.value
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task["error"] = error
            self._save_task(task_id)
        logger.error("Task failed | task_id=%s error=%s", task_id, error)

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            task = self._tasks.get(task_id)
            return dict(task) if task else None

    def run_in_background(
        self,
        task_id: str,
        worker: Callable[[], dict[str, Any]],
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        def _run() -> None:
            with self._job_lock:
                self.mark_running(task_id)
                try:
                    result = worker()
                    self.complete(task_id, result)
                    if on_complete:
                        on_complete()
                except Exception as exc:
                    self.fail(task_id, str(exc))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()


_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
