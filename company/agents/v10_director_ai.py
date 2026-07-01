from typing import Any

from company.core.task import TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


class DirectorAI:
    def __init__(self, executor: TaskExecutor | None = None):
        self.executor = executor or TaskExecutor()

    def run(self, job: Any) -> dict:
        outputs = self._ensure_outputs(job)
        task = TaskFactory.create_task(
            task_type=TaskType.DIRECTION,
            instruction="台本をもとに演出指示を作成してください。",
            input_data={
                "theme": getattr(job, "theme", ""),
                "script": outputs.get("script"),
                "job_id": getattr(job, "job_id", "unknown_job"),
            },
        )

        completed_task = self.executor.execute(task)
        outputs["direction"] = completed_task.output_data
        return completed_task.to_dict()

    def _ensure_outputs(self, job: Any) -> dict:
        if not hasattr(job, "outputs"):
            job.outputs = {}
        return job.outputs
