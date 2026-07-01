from company.core import Employee


class DirectorAI(Employee):
    def __init__(self, brain=None):
        super().__init__(
            name="DirectorAI",
            role="Director",
            brain=brain
        )

    def create_direction(self, script: str) -> str:
        prompt = self._build_prompt(script)
        return self.think(prompt)

    def run(self, job):
        self.log(job, "演出設計を開始します。")

        script = job.get("script_writer", "")
        direction = self.create_direction(script)

        self.update_job(job, "director", direction)
        self.log(job, "演出設計を完了しました。")

        return job

    def _build_prompt(self, script: str) -> str:
        return f"""
あなたはProject SHIROの映像監督Directorです。

以下の台本をもとに、動画の演出指示を作成してください。

台本:
{script}

出力内容:
1. 全体の映像トーン
2. シーンごとの映像内容
3. シーンごとのカメラワーク
4. シーンごとの背景
5. シーンごとのキャラクター表情
6. 字幕表示の方針
7. 画像生成担当Artistへの指示

条件:
・YouTubeショート向け
・5シーン構成
・Stable Diffusionで画像化しやすい内容
・1シーン1枚の画像を前提
・視聴者が飽きないテンポ
・抽象的すぎる表現は禁止
"""


if __name__ == "__main__":
    from company.core import Job
    from company.agents.planner_ai import PlannerAI
    from company.agents.script_writer_ai import ScriptWriterAI

    job = Job("猫の意外な雑学")

    planner = PlannerAI()
    job = planner.run(job)

    writer = ScriptWriterAI()
    job = writer.run(job)

    director = DirectorAI()
    result_job = director.run(job)

    print("DirectorAI Employee対応テスト完了")
    print("director:", result_job.get("director")[:50])