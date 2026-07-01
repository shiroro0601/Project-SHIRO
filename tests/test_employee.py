from company.core import Job, Employee


class TestEmployee(Employee):
    def __init__(self):
        super().__init__(name="TestEmployee", role="Planner")

    def run(self, job):
        self.log(job, "テスト社員が仕事を開始しました。")
        result = self.think("猫の雑学動画を企画してください。")
        self.update_job(job, "planner", result)
        self.log(job, "テスト社員が仕事を完了しました。")
        return job


if __name__ == "__main__":
    job = Job("猫の意外な雑学")
    employee = TestEmployee()
    job = employee.run(job)

    print("Employee基底クラス テスト完了")
    print("job_id:", job.get("job_id"))
    print("planner:", job.get("planner")[:30])
    print("logs:", job.get("logs"))