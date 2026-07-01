from typing import Any

from company.core.task import TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


class ArtistAI:
    def __init__(self, executor: TaskExecutor | None = None):
        self.executor = executor or TaskExecutor()

    def run(self, job: Any) -> dict:
        outputs = self._ensure_outputs(job)
        task = TaskFactory.create_task(
            task_type=TaskType.IMAGE_PROMPT,
            instruction="演出指示をもとに画像生成プロンプトを作成してください。",
            input_data={
                "theme": getattr(job, "theme", ""),
                "direction": outputs.get("direction"),
                "job_id": getattr(job, "job_id", "unknown_job"),
            },
        )

        completed_task = self.executor.execute(task)
        outputs["image_prompt"] = completed_task.output_data
        return completed_task.to_dict()

    def _ensure_outputs(self, job: Any) -> dict:
        if not hasattr(job, "outputs"):
            job.outputs = {}
        return job.outputs
