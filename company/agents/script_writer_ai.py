from company.core import Employee


class ScriptWriterAI(Employee):
    def __init__(self, brain=None):
        super().__init__(
            name="ScriptWriterAI",
            role="ScriptWriter",
            brain=brain
        )

    def write_script(self, plan: str) -> str:
        prompt = self._build_prompt(plan)
        return self.think(prompt)

    def run(self, job):
        self.log(job, "台本作成を開始します。")

        plan = job.get("planner", "")
        script = self.write_script(plan)

        self.update_job(job, "script_writer", script)
        self.log(job, "台本作成を完了しました。")

        return job

    def _build_prompt(self, plan: str) -> str:
        return f"""
あなたはProject SHIROの脚本家ScriptWriterです。

以下の企画をもとに、YouTubeショート動画用の台本を書いてください。

企画:
{plan}

出力内容:
1. 動画タイトル
2. ナレーション台本
3. シーンごとのセリフ
4. 字幕テキスト
5. 視聴維持率を上げるフック
6. ラストの締め

条件:
・日本語
・60秒以内
・5シーン構成
・1シーンあたり短く
・VOICEVOXで読みやすい文章
・字幕にしやすい短文
・テンポ重視
"""


if __name__ == "__main__":
    from company.core import Job
    from company.agents.planner_ai import PlannerAI

    job = Job("猫の意外な雑学")

    planner = PlannerAI()
    job = planner.run(job)

    writer = ScriptWriterAI()
    result_job = writer.run(job)

    print("ScriptWriterAI Employee対応テスト完了")
    print("script_writer:", result_job.get("script_writer")[:50])