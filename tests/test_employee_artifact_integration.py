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


def test_artifact_content_contains_only_artifact_value():
    job = ArtifactJob(job_id="test_artifact_job_002", theme="猫の雑学")

    PlannerAI().run(job)
    ScriptWriterAI().run(job)
    DirectorAI().run(job)
    ArtistAI().run(job)

    assert list(job.outputs["plan"]["content"].keys()) == ["plan"]
    assert list(job.outputs["script"]["content"].keys()) == ["script"]
    assert list(job.outputs["direction"]["content"].keys()) == ["direction"]
    assert list(job.outputs["image_prompt"]["content"].keys()) == ["image_prompt"]

    for artifact in job.outputs.values():
        assert "input_data" not in artifact["content"]
        assert "task_id" not in artifact["content"]
        assert "artifact_id" not in artifact["content"]


def test_artifact_content_has_no_deep_nesting():
    job = ArtifactJob(job_id="test_artifact_job_003", theme="猫の雑学")

    PlannerAI().run(job)
    ScriptWriterAI().run(job)
    DirectorAI().run(job)
    ArtistAI().run(job)

    for key in ["plan", "script", "direction", "image_prompt"]:
        artifact = job.outputs[key]
        assert _max_depth(artifact["content"]) == 1
        assert _count_key_recursive(artifact["content"], "input_data") == 0
        assert _count_key_recursive(artifact["content"], "task_id") == 0
        assert _count_key_recursive(artifact["content"], "artifact_id") == 0
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


def _max_depth(value: Any) -> int:
    if isinstance(value, dict) and value:
        return 1 + max(_max_depth(child) for child in value.values())
    if isinstance(value, list) and value:
        return 1 + max(_max_depth(item) for item in value)
    return 0
