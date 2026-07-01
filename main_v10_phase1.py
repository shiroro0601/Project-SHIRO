from dataclasses import dataclass, field
from typing import Any, Dict, List

from company.core.workflow_v2 import WorkflowV2, WorkflowStep


@dataclass
class Job:
    job_id: str
    theme: str
    status: str = "created"
    history: List[Dict[str, Any]] = field(default_factory=list)


class PlannerAI:
    def run(self, job: Job):
        print("[PlannerAI] 企画を作成しました。")
        return {
            "plan": f"{job.theme}についての動画企画",
        }


class ScriptWriterAI:
    def run(self, job: Job):
        print("[ScriptWriterAI] 台本を作成しました。")
        return {
            "script": f"{job.theme}について、視聴者が驚く短い台本",
        }


class DirectorAI:
    def run(self, job: Job):
        print("[DirectorAI] 演出指示を作成しました。")
        return {
            "direction": f"{job.theme}をテンポよく見せる演出",
        }


class ArtistAI:
    def run(self, job: Job):
        print("[ArtistAI] 画像生成指示を作成しました。")
        return {
            "image_prompt": f"high quality illustration about {job.theme}",
        }


def main():
    print("================================")
    print("Project SHIRO Version1.0 Phase1")
    print("Workflow V2 起動")
    print("================================")

    job = Job(
        job_id="job_v10_phase1_001",
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
    print("================================")
    print("Workflow V2 実行結果")
    print("================================")
    print(f"job_id: {result.job_id}")
    print(f"status: {result.status.value}")

    print("")
    print("Step Results")
    print("--------------------------------")

    for step_result in result.step_results:
        print(f"step: {step_result.step_name}")
        print(f"status: {step_result.status.value}")
        print(f"output: {step_result.output}")
        print("--------------------------------")

    print("")
    print("Job History")
    print("--------------------------------")
    for history in job.history:
        print(history)


if __name__ == "__main__":
    main()