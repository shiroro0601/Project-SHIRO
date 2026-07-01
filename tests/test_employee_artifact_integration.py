from dataclasses import dataclass, field
from typing import Any, Dict, List

from company.agents.v10_artist_ai import ArtistAI
from company.agents.v10_director_ai import DirectorAI
from company.agents.v10_planner_ai import PlannerAI
from company.agents.v10_script_writer_ai import ScriptWriterAI
from company.core.job_status import JobStatus
from company.core.workflow_v2 import WorkflowStep, WorkflowV2


@dataclass
class ArtifactJob:
    job_id: str
    theme: str
    status: str = "created"
    outputs: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)


def test_workflow_v2_runs_v10_employees_and_saves_artifacts():
    job = ArtifactJob(job_id="test_artifact_job_001", theme="猫の雑学")
    workflow = WorkflowV2(
        steps=[
            WorkflowStep(name="PlannerAI", employee=PlannerAI()),
            WorkflowStep(name="ScriptWriterAI", employee=ScriptWriterAI()),
            WorkflowStep(name="DirectorAI", employee=DirectorAI()),
            WorkflowStep(name="ArtistAI", employee=ArtistAI()),
        ]
    )

    result = workflow.run(job)

    assert result.status == JobStatus.COMPLETED
    assert list(job.outputs.keys()) == ["plan", "script", "direction", "image_prompt"]
    assert all(step.output["status"] == "completed" for step in result.step_results)

    for key in ["plan", "script", "direction", "image_prompt"]:
        artifact = job.outputs[key]
        assert artifact["artifact_id"].startswith(f"artifact_{artifact['artifact_type']}_")
        assert artifact["artifact_type"] == key
        assert artifact["name"] == key
        assert "content" in artifact
        assert artifact["source_task_id"] is not None
        assert artifact["created_at"] is not None


def test_next_employee_receives_previous_artifact_content_only():
    job = ArtifactJob(job_id="test_artifact_job_002", theme="猫の雑学")

    PlannerAI().run(job)
    ScriptWriterAI().run(job)
    DirectorAI().run(job)
    ArtistAI().run(job)

    plan_artifact = job.outputs["plan"]
    script_artifact = job.outputs["script"]
    direction_artifact = job.outputs["direction"]
    image_prompt_artifact = job.outputs["image_prompt"]

    assert script_artifact["content"]["input_data"]["plan"] == plan_artifact["content"]
    assert direction_artifact["content"]["input_data"]["script"] == script_artifact["content"]
    assert image_prompt_artifact["content"]["input_data"]["direction"] == direction_artifact["content"]

    assert "artifact_id" not in script_artifact["content"]["input_data"]["plan"]
    assert "artifact_id" not in direction_artifact["content"]["input_data"]["script"]
    assert "artifact_id" not in image_prompt_artifact["content"]["input_data"]["direction"]


def test_task_id_nesting_does_not_grow_through_artifacts():
    job = ArtifactJob(job_id="test_artifact_job_003", theme="猫の雑学")

    PlannerAI().run(job)
    ScriptWriterAI().run(job)
    DirectorAI().run(job)
    ArtistAI().run(job)

    for key in ["plan", "script", "direction", "image_prompt"]:
        artifact = job.outputs[key]
        assert _count_key_recursive(artifact, "task_id") <= 2
        assert _count_key_recursive(artifact, "artifact_id") == 1


def _count_key_recursive(value: Any, target_key: str) -> int:
    if isinstance(value, dict):
        return sum(
            (1 if key == target_key else 0) + _count_key_recursive(child, target_key)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return sum(_count_key_recursive(item, target_key) for item in value)
    return 0
