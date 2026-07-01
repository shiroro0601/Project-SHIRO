class Workflow:
    def __init__(self, name: str = "DefaultWorkflow"):
        self.name = name
        self.steps = []

    def add_step(self, employee):
        self.steps.append(employee)

    def run(self, job):
        job.update_status("running")
        job.log(f"[Workflow] {self.name} started")

        for employee in self.steps:
            job.log(f"[Workflow] {employee.name} started")

            try:
                job = employee.run(job)
                job.log(f"[Workflow] {employee.name} completed")

            except Exception as e:
                job.update_status("failed")
                job.log(f"[Workflow] {employee.name} failed: {e}")
                raise e

        job.update_status("completed")
        job.log(f"[Workflow] {self.name} completed")

        return job