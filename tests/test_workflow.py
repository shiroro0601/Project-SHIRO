from company.core import Job, Employee, Workflow


class TestPlanner(Employee):
    def __init__(self):
        super().__init__(name="TestPlanner", role="Planner")

    def run(self, job):
        self.log(job, "企画を作成します。")
        result = self.think("猫の雑学ショート動画を企画してください。")
        self.update_job(job, "planner", result)
        return job


class TestScriptWriter(Employee):
    def __init__(self):
        super().__init__(name="TestScriptWriter", role="ScriptWriter")

    def run(self, job):
        self.log(job, "台本を作成します。")
        planner_result = job.get("planner", "")
        result = self.think(f"以下の企画をもとに台本を書いてください。\n{planner_result}")
        self.update_job(job, "script_writer", result)
        return job


if __name__ == "__main__":
    job = Job("猫の意外な雑学")

    workflow = Workflow(name="TestVideoWorkflow")
    workflow.add_step(TestPlanner())
    workflow.add_step(TestScriptWriter())

    result_job = workflow.run(job)

    print("Workflow Engine テスト完了")
    print("job_id:", result_job.get("job_id"))
    print("status:", result_job.get("status"))
    print("planner:", result_job.get("planner")[:30])
    print("script_writer:", result_job.get("script_writer")[:30])
    print("logs:", result_job.get("logs"))