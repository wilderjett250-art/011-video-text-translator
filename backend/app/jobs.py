import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict

from .models import JobState, now_iso


class JobManager:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._jobs: Dict[str, JobState] = {}
        self._lock = threading.Lock()

    def submit(self, kind: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> JobState:
        job = JobState(
            id=uuid.uuid4().hex,
            kind=kind,
            status="queued",
            created_at=now_iso(),
            updated_at=now_iso(),
            message="等待处理",
        )
        with self._lock:
            self._jobs[job.id] = job
        self._executor.submit(self._run, job.id, fn, args, kwargs)
        return job

    def get(self, job_id: str) -> JobState:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            return self._jobs[job_id]

    def update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            payload = job.dict()
            payload.update(changes)
            payload["updated_at"] = now_iso()
            self._jobs[job_id] = JobState(**payload)

    def _run(self, job_id: str, fn: Callable[..., Any], args: Any, kwargs: Any) -> None:
        self.update(job_id, status="running", message="处理中", progress=0.02)
        try:
            result = fn(job_id, self, *args, **kwargs)
            self.update(job_id, status="done", message="完成", progress=1, result=result)
        except Exception as exc:  # noqa: BLE001
            self.update(
                job_id,
                status="failed",
                message="处理失败",
                error=f"{exc}\n{traceback.format_exc()}",
            )


job_manager = JobManager()

