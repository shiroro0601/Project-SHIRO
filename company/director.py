"""
Project SHIRO v0.8
演出部
"""

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact
from company.llm import LLM


class Director(Employee):
    """
    演出部AI
    台本をシーンごとに分割する社員
    """

    def __init__(self):
        super().__init__(
            name="Director AI",
            department="演出"
        )
        self.llm = LLM()

    def run(self, task: Task) -> Artifact:
        self.log("シーン分割を開始しました。")

        script = task.data.get("script", "")

        prompt = f"""
以下の台本をシーン分割してください。

{script}
"""

        response = self.llm.chat(
            role="director",
            prompt=prompt
        )

        scenes = self._parse_scenes(response)

        return Artifact(
            artifact_type="scenes",
            content=scenes,
            metadata={
                "source_script": script,
                "scene_count": len(scenes),
                "department": self.department,
                "employee": self.name,
            }
        )

    def _parse_scenes(self, text: str) -> list:
        """
        LLMの出力をシーンリストへ変換する
        形式：
        番号|タイトル|本文|画像プロンプト
        """

        scenes = []

        lines = text.strip().splitlines()

        for line in lines:
            parts = line.split("|")

            if len(parts) != 4:
                continue

            scene_number = int(parts[0].strip())
            title = parts[1].strip()
            scene_text = parts[2].strip()
            image_prompt = parts[3].strip()

            scenes.append(
                {
                    "scene_number": scene_number,
                    "title": title,
                    "text": scene_text,
                    "image_prompt": image_prompt,
                }
            )

        return scenes