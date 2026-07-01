from typing import Any

from company.core.artifact import ArtifactFactory, ArtifactType
from company.core.task import TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


class ScriptWriterAI:
    def __init__(self, executor: TaskExecutor | None = None):
        self.executor = executor or TaskExecutor()

    def run(self, job: Any) -> dict:
        outputs = self._ensure_outputs(job)
        plan_artifact = outputs.get("plan", {})
        task = TaskFactory.create_task(
            task_type=TaskType.SCRIPT_WRITING,
            instruction="企画をもとに台本を作成してください。",
            input_data={
                "theme": getattr(job, "theme", ""),
                "plan": plan_artifact.get("content", {}).get("plan"),
                "job_id": getattr(job, "job_id", "unknown_job"),
            },
        )

        completed_task = self.executor.execute(task)
        artifact = ArtifactFactory.create_artifact(
            artifact_type=ArtifactType.SCRIPT,
            name="script",
            content=self._artifact_content(completed_task.output_data),
            source_task_id=completed_task.task_id,
        )
        outputs["script"] = artifact.to_dict()
        return completed_task.to_dict()

    def _ensure_outputs(self, job: Any) -> dict:
        if not hasattr(job, "outputs"):
            job.outputs = {}
        return job.outputs

    def _artifact_content(self, output_data: dict) -> dict:
        return {
            "script": output_data.get("result"),
        }
