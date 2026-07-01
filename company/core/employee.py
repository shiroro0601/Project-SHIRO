from company.brain import Brain


class Employee:
    def __init__(self, name: str, role: str, brain=None):
        self.name = name
        self.role = role
        self.brain = brain or Brain(provider="dummy", model="shiro-local")

    def run(self, job):
        raise NotImplementedError("各社員クラスでrun(job)を実装してください。")

    def think(self, prompt: str) -> str:
        return self.brain.ask(role=self.role, prompt=prompt)

    def log(self, job, message: str):
        if hasattr(job, "log"):
            job.log(f"[{self.name}] {message}")

    def update_job(self, job, section: str, content):
        if hasattr(job, "update_section"):
            job.update_section(section, content)