from company.core import Employee


class PlannerAI(Employee):
    def __init__(self, brain=None):
        super().__init__(
            name="PlannerAI",
            role="Planner",
            brain=brain
        )

    def create_plan(self, theme: str) -> str:
        prompt = self._build_prompt(theme)
        return self.think(prompt)

    def run(self, job):
        self.log(job, "企画作成を開始します。")

        theme = job.get("theme", "")
        plan = self.create_plan(theme)

        self.update_job(job, "planner", plan)
        self.log(job, "企画作成を完了しました。")

        return job

    def _build_prompt(self, theme: str) -> str:
        return f"""
あなたはProject SHIROの企画担当Plannerです。

以下のテーマでYouTubeショート動画の企画を作ってください。

テーマ:
{theme}

出力内容:
1. 動画タイトル
2. 狙う視聴者
3. 動画の目的
4. 5シーン構成
5. 視聴維持率を上げる工夫
6. サムネイル案
7. 最後の一言

条件:
・日本語
・ショート動画向け
・テンポ重視
・実際に動画化しやすい内容
"""


if __name__ == "__main__":
    from company.core import Job

    job = Job("猫の意外な雑学")
    planner = PlannerAI()
    result_job = planner.run(job)

    print("PlannerAI Employee対応テスト完了")
    print("planner:", result_job.get("planner")[:50])