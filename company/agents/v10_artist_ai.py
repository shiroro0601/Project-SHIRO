from typing import Any

from company.core.artifact import ArtifactFactory, ArtifactType
from company.core.task import TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


class ArtistAI:
    def __init__(self, executor: TaskExecutor | None = None):
        self.executor = executor or TaskExecutor()

    def run(self, job: Any) -> dict:
        outputs = self._ensure_outputs(job)
        direction_artifact = outputs.get("direction", {})
        task = TaskFactory.create_task(
            task_type=TaskType.IMAGE_PROMPT,
            instruction="演出指示をもとに画像生成プロンプトを作成してください。",
            input_data={
                "theme": getattr(job, "theme", ""),
                "direction": direction_artifact.get("content"),
                "job_id": getattr(job, "job_id", "unknown_job"),
            },
        )

        completed_task = self.executor.execute(task)
        artifact = ArtifactFactory.create_artifact(
            artifact_type=ArtifactType.IMAGE_PROMPT,
            name="image_prompt",
            content=self._artifact_content(completed_task.output_data),
            source_task_id=completed_task.task_id,
        )
        outputs["image_prompt"] = artifact.to_dict()
        return completed_task.to_dict()

    def _ensure_outputs(self, job: Any) -> dict:
        if not hasattr(job, "outputs"):
            job.outputs = {}
        return job.outputs

    def _artifact_content(self, output_data: dict) -> dict:
        return {
            "task_type": output_data.get("task_type"),
            "instruction": output_data.get("instruction"),
            "input_data": output_data.get("input_data", {}),
            "result": output_data.get("result"),
        }
