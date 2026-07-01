from dataclasses import dataclass, field
from typing import Any, Dict, List

from company.agents.v10_artist_ai import ArtistAI
from company.agents.v10_director_ai import DirectorAI
from company.agents.v10_planner_ai import PlannerAI
from company.agents.v10_script_writer_ai import ScriptWriterAI
from company.core.job_status import JobStatus
from company.core.workflow_v2 import WorkflowStep, WorkflowV2


@dataclass
class EmployeeExecutorJob:
    job_id: str
    theme: str
    status: str = "created"
    outputs: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)


def test_planner_ai_creates_plan_output():
    job = EmployeeExecutorJob(job_id="test_job_001", theme="猫の雑学")

    result = PlannerAI().run(job)

    assert result["status"] == "completed"
    assert result["task_type"] == "planning"
    assert "plan" in job.outputs
    assert job.outputs["plan"]["task_type"] == "planning"


def test_script_writer_ai_creates_script_output():
    job = EmployeeExecutorJob(job_id="test_job_002", theme="猫の雑学")
    PlannerAI().run(job)

    result = ScriptWriterAI().run(job)

    assert result["status"] == "completed"
    assert result["task_type"] == "script_writing"
    assert "script" in job.outputs
    assert job.outputs["script"]["input_data"]["plan"] == job.outputs["plan"]


def test_director_ai_creates_direction_output():
    job = EmployeeExecutorJob(job_id="test_job_003", theme="猫の雑学")
    PlannerAI().run(job)
    ScriptWriterAI().run(job)

    result = DirectorAI().run(job)

    assert result["status"] == "completed"
    assert result["task_type"] == "direction"
    assert "direction" in job.outputs
    assert job.outputs["direction"]["input_data"]["script"] == job.outputs["script"]


def test_artist_ai_creates_image_prompt_output():
    job = EmployeeExecutorJob(job_id="test_job_004", theme="猫の雑学")
    PlannerAI().run(job)
    ScriptWriterAI().run(job)
    DirectorAI().run(job)

    result = ArtistAI().run(job)

    assert result["status"] == "completed"
    assert result["task_type"] == "image_prompt"
    assert "image_prompt" in job.outputs
    assert job.outputs["image_prompt"]["input_data"]["direction"] == job.outputs["direction"]


def test_workflow_v2_runs_v10_employees_in_order():
    job = EmployeeExecutorJob(job_id="test_job_005", theme="猫の雑学")
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
    assert job.status == JobStatus.COMPLETED.value
    assert list(job.outputs.keys()) == ["plan", "script", "direction", "image_prompt"]
    assert [step.step_name for step in result.step_results] == [
        "PlannerAI",
        "ScriptWriterAI",
        "DirectorAI",
        "ArtistAI",
    ]
    assert all(step.output["status"] == "completed" for step in result.step_results)
