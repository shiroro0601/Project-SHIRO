"""
Project SHIRO v0.8
企画部
"""

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact
from company.llm import LLM


class Planner(Employee):
    """
    企画部AI
    """

    def __init__(self):
        super().__init__(
            name="Planner AI",
            department="企画"
        )
        self.llm = LLM()

    def run(self, task: Task) -> Artifact:
        self.log("企画を開始しました。")

        prompt = task.description

        idea = self.llm.chat(
            role="planner",
            prompt=prompt
        )

        return Artifact(
            artifact_type="plan",
            content=idea,
            metadata={
                "source_task": task.title,
                "department": self.department,
                "employee": self.name,
            }
        )