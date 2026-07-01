"""
Project SHIRO v0.8
脚本部
"""

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact
from company.llm import LLM


class ScriptWriter(Employee):
    """
    脚本部AI
    """

    def __init__(self):
        super().__init__(
            name="Script Writer AI",
            department="脚本"
        )
        self.llm = LLM()

    def run(self, task: Task) -> Artifact:
        self.log("脚本作成を開始しました。")

        plan = task.data.get("plan", "")

        prompt = f"""
以下の企画をもとにYouTube動画の台本を作ってください。

{plan}
"""

        script = self.llm.chat(
            role="script_writer",
            prompt=prompt
        )

        return Artifact(
            artifact_type="script",
            content=script,
            metadata={
                "source_plan": plan,
                "department": self.department,
                "employee": self.name,
            }
        )