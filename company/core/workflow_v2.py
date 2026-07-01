from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from company.core.job_status import JobStatus, StepStatus


@dataclass
class WorkflowStepResult:
    step_name: str
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass
class WorkflowStep:
    name: str
    employee: Any
    method_name: str = "run"
    required: bool = True


@dataclass
class WorkflowV2Result:
    job_id: str
    status: JobStatus
    step_results: List[WorkflowStepResult] = field(default_factory=list)
    error: Optional[str] = None


class WorkflowV2:
    """
    Project SHIRO Version1.0 Workflow V2

    目的:
    - Job状態管理
    - Step状態管理
    - エラー処理
    - 自動停止
    - 将来的な条件分岐・並列実行・リトライへの拡張

    設計方針:
    - 既存Workflowを壊さない
    - Step単位で社員を差し替え可能
    - employee.run(job) 形式を標準にする
    """

    def __init__(self, steps: List[WorkflowStep], stop_on_error: bool = True):
        self.steps = steps
        self.stop_on_error = stop_on_error

    def run(self, job: Any) -> WorkflowV2Result:
        job_id = self._get_job_id(job)
        self._set_job_status(job, JobStatus.RUNNING)

        step_results: List[WorkflowStepResult] = []

        for step in self.steps:
            result = self._run_step(step, job)
            step_results.append(result)

            if result.status == StepStatus.FAILED:
                if step.required or self.stop_on_error:
                    self._set_job_status(job, JobStatus.FAILED)
                    return WorkflowV2Result(
                        job_id=job_id,
                        status=JobStatus.FAILED,
                        step_results=step_results,
                        error=result.error,
                    )

        self._set_job_status(job, JobStatus.COMPLETED)

        return WorkflowV2Result(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            step_results=step_results,
        )

    def _run_step(self, step: WorkflowStep, job: Any) -> WorkflowStepResult:
        started_at = self._now()

        result = WorkflowStepResult(
            step_name=step.name,
            status=StepStatus.RUNNING,
            started_at=started_at,
        )

        try:
            method = getattr(step.employee, step.method_name)

            output = method(job)

            result.status = StepStatus.COMPLETED
            result.output = output
            result.finished_at = self._now()

            self._append_job_history(
                job,
                {
                    "step": step.name,
                    "status": StepStatus.COMPLETED.value,
                    "started_at": result.started_at,
                    "finished_at": result.finished_at,
                },
            )

            return result

        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            result.finished_at = self._now()

            self._append_job_history(
                job,
                {
                    "step": step.name,
                    "status": StepStatus.FAILED.value,
                    "error": str(e),
                    "started_at": result.started_at,
                    "finished_at": result.finished_at,
                },
            )

            return result

    def _get_job_id(self, job: Any) -> str:
        if hasattr(job, "job_id"):
            return str(job.job_id)
        if hasattr(job, "id"):
            return str(job.id)
        return "unknown_job"

    def _set_job_status(self, job: Any, status: JobStatus) -> None:
        if hasattr(job, "status"):
            job.status = status.value
        else:
            setattr(job, "status", status.value)

    def _append_job_history(self, job: Any, record: Dict[str, Any]) -> None:
        if not hasattr(job, "history"):
            setattr(job, "history", [])

        job.history.append(record)

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")