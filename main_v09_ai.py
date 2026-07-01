from company.brain import Brain
from company.core import Job, Workflow
from company.memory import CompanyMemory
from company.agents.planner_ai import PlannerAI
from company.agents.script_writer_ai import ScriptWriterAI
from company.agents.director_ai import DirectorAI
from company.agents.artist_ai import ArtistAI


class ProjectShiroV09:
    def __init__(self):
        self.brain = Brain(provider="dummy", model="shiro-local")
        self.memory = CompanyMemory()

        self.workflow = Workflow(name="Project SHIRO AI Video Workflow")
        self.workflow.add_step(PlannerAI(brain=self.brain))
        self.workflow.add_step(ScriptWriterAI(brain=self.brain))
        self.workflow.add_step(DirectorAI(brain=self.brain))
        self.workflow.add_step(ArtistAI(brain=self.brain))

    def run(self, theme: str):
        print("================================")
        print("Project SHIRO Version0.9 AI会社 起動")
        print("================================")
        print(f"テーマ: {theme}")
        print()

        job = Job(theme)
        print("[CEO] Jobを作成しました:", job.get("job_id"))

        print("[CEO] Workflowへ仕事を渡します。")
        result_job = self.workflow.run(job)

        saved_job_id = self.memory.save_job(result_job)

        print()
        print("================================")
        print("Version0.9 Workflow + Job Memory 統合テスト 完了")
        print("================================")
        print("job_id:", saved_job_id)
        print("status:", result_job.get("status"))
        print("保存先: outputs/memory/company_memory.json")

        return result_job


if __name__ == "__main__":
    app = ProjectShiroV09()
    app.run("猫の意外な雑学")