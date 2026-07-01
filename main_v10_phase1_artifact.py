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
    print("Project SHIRO Version1.0 Phase1-5")
    print("Artifact Layer")
    print("================================")

    job = Job(
        job_id="job_v10_phase1_005",
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
    print("Workflow Result")
    print("--------------------------------")
    print(f"job_id: {result.job_id}")
    print(f"status: {result.status.value}")

    print("")
    print("Artifacts")
    print("--------------------------------")
    for key, artifact in job.outputs.items():
        print(f"{key}:")
        print(f"  artifact_id: {artifact['artifact_id']}")
        print(f"  artifact_type: {artifact['artifact_type']}")
        print(f"  source_task_id: {artifact['source_task_id']}")
        print("  content.input_data:")
        pprint(artifact["content"].get("input_data", {}), indent=4)
        print("--------------------------------")


if __name__ == "__main__":
    main()
