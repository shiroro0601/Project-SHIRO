from dataclasses import dataclass, field
from pprint import pprint
from typing import Any, Dict, List

from company.agents.v10_artist_ai import ArtistAI
from company.agents.v10_director_ai import DirectorAI
from company.agents.v10_planner_ai import PlannerAI
from company.agents.v10_script_writer_ai import ScriptWriterAI
from company.core.workflow_v2 import WorkflowStep, WorkflowV2


@dataclass
class Job:
    job_id: str
    theme: str
    status: str = "created"
    outputs: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)


def main():
    print("================================")
    print("Project SHIRO Version1.0 Phase1-4")
    print("Employee -> TaskExecutor 接続")
    print("================================")

    job = Job(
        job_id="job_v10_phase1_004",
        theme="猫の意外な雑学",
    )

    workflow = WorkflowV2(
        steps=[
            WorkflowStep(name="PlannerAI", employee=PlannerAI()),
            WorkflowStep(name="ScriptWriterAI", employee=ScriptWriterAI()),
            WorkflowStep(name="DirectorAI", employee=DirectorAI()),
            WorkflowStep(name="ArtistAI", employee=ArtistAI()),
        ],
        stop_on_error=True,
    )

    result = workflow.run(job)

    print("")
    print("Job Outputs")
    print("--------------------------------")
    pprint(job.outputs)

    print("")
    print("Workflow Result")
    print("--------------------------------")
    print(f"job_id: {result.job_id}")
    print(f"status: {result.status.value}")

    print("")
    print("Step Results")
    print("--------------------------------")
    for step_result in result.step_results:
        print(f"step: {step_result.step_name}")
        print(f"status: {step_result.status.value}")
        pprint(step_result.output)
        print("--------------------------------")


if __name__ == "__main__":
    main()
