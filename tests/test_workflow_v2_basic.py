from dataclasses import dataclass, field
from typing import List, Dict, Any

from company.core.workflow_v2 import WorkflowV2, WorkflowStep
from company.core.job_status import JobStatus


@dataclass
class TestJob:
    job_id: str
    theme: str
    status: str = "created"
    history: List[Dict[str, Any]] = field(default_factory=list)


class SuccessEmployee:
    def __init__(self, name: str):
        self.name = name

    def run(self, job: TestJob):
        return f"{self.name} completed: {job.theme}"


class FailingEmployee:
    def run(self, job: TestJob):
        raise RuntimeError("意図的なテストエラー")


def test_workflow_v2_success():
    job = TestJob(
        job_id="test_job_001",
        theme="猫の雑学",
    )

    workflow = WorkflowV2(
        steps=[
            WorkflowStep(name="Planner", employee=SuccessEmployee("Planner")),
            WorkflowStep(name="ScriptWriter", employee=SuccessEmployee("ScriptWriter")),
            WorkflowStep(name="Director", employee=SuccessEmployee("Director")),
        ]
    )

    result = workflow.run(job)

    assert result.status == JobStatus.COMPLETED
    assert job.status == JobStatus.COMPLETED.value
    assert len(result.step_results) == 3
    assert len(job.history) == 3
    assert job.history[0]["step"] == "Planner"


def test_workflow_v2_error_stop():
    job = TestJob(
        job_id="test_job_002",
        theme="犬の雑学",
    )

    workflow = WorkflowV2(
        steps=[
            WorkflowStep(name="Planner", employee=SuccessEmployee("Planner")),
            WorkflowStep(name="ScriptWriter", employee=FailingEmployee()),
            WorkflowStep(name="Director", employee=SuccessEmployee("Director")),
        ],
        stop_on_error=True,
    )

    result = workflow.run(job)

    assert result.status == JobStatus.FAILED
    assert job.status == JobStatus.FAILED.value
    assert len(result.step_results) == 2
    assert result.error == "意図的なテストエラー"
    assert len(job.history) == 2